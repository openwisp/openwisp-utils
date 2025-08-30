import os
import shutil
import subprocess
import sys
import time
from datetime import datetime

import questionary
import requests
from openwisp_utils.releaser.changelog import (
    format_rst_block,
    get_release_block_from_file,
    process_changelog,
    run_git_cliff,
    update_changelog_file,
)
from openwisp_utils.releaser.config import load_config
from openwisp_utils.releaser.github import GitHub
from openwisp_utils.releaser.utils import (
    adjust_markdown_headings,
    demote_markdown_headings,
    format_file_with_docstrfmt,
    get_current_branch,
    rst_to_markdown,
)
from openwisp_utils.releaser.version import (
    bump_version,
    determine_new_version,
    get_current_version,
)

MAIN_BRANCHES = ["master", "main"]


def check_prerequisites():
    """Checks for all required prerequisite."""
    print("🔎 Checking prerequisites...")
    checks = []
    config = None
    gh = None

    tools = ["git", "git-cliff", "docstrfmt"]
    for tool in tools:
        is_installed = shutil.which(tool) is not None
        checks.append((is_installed, f"Tool `{tool}` is installed."))

    token = os.environ.get("OW_GITHUB_TOKEN")
    checks.append((token is not None, "OW_GITHUB_TOKEN environment variable is set."))

    try:
        config = load_config()
        checks.append((True, "Configuration loaded successfully."))
    except FileNotFoundError as e:
        checks.append((False, f"Failed to load configuration | {str(e)}"))

    if config and config.get("repo"):
        checks.append((True, f"Repository '{config['repo']}' is found from origin."))
    else:
        checks.append(
            (
                False,
                "Repository was not found with git. Please set git remote repository on origin.",
            )
        )

    if token and config and config.get("repo"):
        gh = GitHub(token, repo=config["repo"])
        if gh.check_pr_creation_permission():
            checks.append(
                (True, f"GitHub token has access to the '{config['repo']}' repository.")
            )
        else:
            error_message = f"GitHub token is missing PR write access to the '{config['repo']}' repository."
            checks.append((False, error_message))

    all_passed = True
    for passed, message in checks:
        if passed:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
            all_passed = False

    if not all_passed:
        print("\nPlease fix the missing prerequisites and try again.")
        sys.exit(1)

    return config, gh


def get_ai_summary(content, file_format, token):
    # Asks the user if they want to use GPT for summarizing the changelog,
    # and handles the interaction loop (Accept/Retry/Use Original).
    if not questionary.confirm(
        "Do you want to use an AI to generate a human-readable summary of the changelog?"
    ).ask():
        return content

    if not token:
        print(
            "⚠️ OPENAI_CHATGPT_TOKEN environment variable is not set. Skipping AI summary.",
            file=sys.stderr,
        )
        return content

    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    prompt = (
        f"Please generate a human-readable changelog from the following git-cliff output. "
        f"The final output should be in {file_format} format and should only contain the changelog content, "
        f"ready to be inserted into a CHANGES.{file_format} file. Do not include any extra commentary.\n\n"
        f"Here is the content to process:\n\n{content}"
    )
    payload = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
    }

    while True:
        try:
            print("🤖 Generating AI summary... (this might take a moment)")
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            summary = response.json()["choices"][0]["message"]["content"]

            print("\n" + "=" * 20 + " AI Generated Summary " + "=" * 20)
            print(summary)
            print("=" * 62)

            decision = questionary.select(
                "How would you like to proceed?",
                choices=["Accept", "Retry", "Use Original (from git-cliff)"],
            ).ask()

            if decision == "Accept":
                return summary
            elif decision == "Use Original (from git-cliff)":
                return content
            elif decision == "Retry":
                continue
            else:
                return content
        except requests.RequestException as e:
            print(f"\n⚠️ An error occurred with the AI API: {e}", file=sys.stderr)
            return content


def port_changelog_to_main(gh, config, version, changelog_body, original_branch):
    """Checks out the main branch, updates the changelog, and creates a new PR."""
    print("\n" + "=" * 50)
    print("🤖 Starting Changelog Porting Process")
    print("=" * 50)

    is_md = config["changelog_path"].endswith(".md")
    changelog_date_str = datetime.now().strftime("%Y-%m-%d")

    if is_md:
        version_header = f"## Version {version} [{changelog_date_str}]"
        # The body has already been adjusted for the file, so no heading changes are needed.
        full_block_to_port = f"{version_header}\n\n{changelog_body}"
    else:  # rst
        version_header = f"Version {version}  [{changelog_date_str}]"
        underline = "-" * len(version_header)
        full_block_to_port = f"{version_header}\n{underline}\n\n{changelog_body}"

    try:
        main_branch = questionary.select(
            "Which branch should the changelog be ported to?",
            choices=MAIN_BRANCHES,
        ).ask()

        if not main_branch:
            print("Porting cancelled.")
            return

        port_branch = f"chore/port-changelog-{version}"
        commit_message = f"[docs] Port changelog for {version}"
        pr_title = f"[docs] Port changelog for release {version}"

        print(f"Checking out '{main_branch}' and pulling latest changes...")
        subprocess.run(
            ["git", "checkout", main_branch], check=True, capture_output=True
        )
        subprocess.run(
            ["git", "pull", "origin", main_branch], check=True, capture_output=True
        )

        print(f"Creating new branch '{port_branch}'...")
        subprocess.run(
            ["git", "checkout", "-b", port_branch], check=True, capture_output=True
        )

        print("Updating changelog file...")
        update_changelog_file(
            config["changelog_path"], full_block_to_port, is_port=True
        )

        # Format the file after porting, if it's an RST file
        if config["changelog_path"].endswith(".rst"):
            format_file_with_docstrfmt(config["changelog_path"])

        print("Committing changes...")
        subprocess.run(
            ["git", "add", config["changelog_path"]], check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", commit_message], check=True, capture_output=True
        )

        print(f"Pushing branch '{port_branch}' to origin...")
        subprocess.run(
            ["git", "push", "origin", port_branch], check=True, capture_output=True
        )

        print("Creating pull request...")
        pr_url = gh.create_pr(port_branch, main_branch, pr_title)
        print(f"\n✅ Successfully created Pull Request for changelog port: {pr_url}")

    finally:
        print(f"\nSwitching back to original branch '{original_branch}'...")
        subprocess.run(
            ["git", "checkout", original_branch], check=True, capture_output=True
        )


def main():
    config, gh = check_prerequisites()
    original_branch = get_current_branch()
    is_bugfix = original_branch not in MAIN_BRANCHES
    release_type = "Bugfix" if is_bugfix else "Feature"

    current_version, current_type = get_current_version(config)
    new_version = determine_new_version(current_version, current_type, is_bugfix)

    if not new_version:
        print("No version provided. Release cancelled.")
        sys.exit(0)

    print(
        f"🚀 Starting {release_type} Release Flow "
        f"for version {new_version} on branch '{original_branch}'..."
    )

    raw_changelog_block = run_git_cliff(new_version)
    raw_changelog_block = raw_changelog_block.replace("#REPO#", config["repo"])
    if not raw_changelog_block:
        print("No changes found for the new release. Exiting.")
        sys.exit(0)

    processed_block = process_changelog(raw_changelog_block)

    print("\n📝  Generated and Formatted Changelog Block:\n")
    formatted_block_rst = format_rst_block(processed_block)

    gpt_token = os.environ.get("OPENAI_CHATGPT_TOKEN")
    final_formatted_block = get_ai_summary(
        formatted_block_rst, config["changelog_format"], gpt_token
    )

    print("\n📝  Generated and Formatted Changelog Block:\n")
    print(final_formatted_block)

    if not questionary.confirm("Accept this block and proceed?").ask():
        print("Release cancelled.")
        sys.exit(0)

    changelog_date_str = datetime.now().strftime("%Y-%m-%d")
    tag_date_str = datetime.now().strftime("%d-%m-%Y")
    changelog_path = config["changelog_path"]

    if config["changelog_format"] == "md":
        final_formatted_block = rst_to_markdown(final_formatted_block)
        final_formatted_block = adjust_markdown_headings(final_formatted_block)
        final_formatted_block = (
            final_formatted_block.replace("\\#", "#")
            .replace("\\[", "[")
            .replace("\\]", "]")
        )

    update_changelog_file(changelog_path, final_formatted_block)

    # Format the file after changelog addition
    if config["changelog_format"] == "rst":
        format_file_with_docstrfmt(changelog_path)

    print(f"✅ {changelog_path} has been updated.")

    was_bumped = bump_version(config, new_version)
    if was_bumped:
        print(f"✅ Version bumped to {new_version} and set to 'final'.")
    else:
        print("\n" + "=" * 60)
        print("⚠️  The version number could not be bumped automatically.")
        print("   Please bump it manually before the changelog is committed.")
        questionary.confirm(
            "Press Enter when you have bumped the version number..."
        ).ask()
        print("=" * 60)

    print(
        f"\n👀 Please review the updated '{changelog_path}' and any version files, making final edits."
    )
    questionary.confirm("Press Enter when you have finished editing...").ask()

    print("\nReading final changelog content from disk...")
    latest_changelog_block = get_release_block_from_file(changelog_path, new_version)
    if not latest_changelog_block:
        print(
            "\nWarning: Could not re-read the changelog block. Using initially generated content.",
            file=sys.stderr,
        )
        latest_changelog_block = final_formatted_block

    if config["changelog_format"] == "rst":
        format_file_with_docstrfmt(changelog_path)

    release_branch = f"release/{new_version}"
    pr_title = f"[release] Version {new_version}"
    subprocess.run(
        ["git", "checkout", "-b", release_branch], check=True, capture_output=True
    )

    print("Adding all changed files to git...")
    subprocess.run(["git", "add", "."], check=True, capture_output=True)

    commit_message = f"{new_version} release"
    subprocess.run(
        ["git", "commit", "-m", commit_message], check=True, capture_output=True
    )
    print("✅ Changes committed to the release branch.")

    print(f"⤴️  Pushing new branch '{release_branch}' to GitHub...")
    subprocess.run(
        ["git", "push", "origin", release_branch], check=True, capture_output=True
    )

    pr_url = gh.create_pr(release_branch, original_branch, pr_title)
    print(f" Pull Request created: {pr_url}")

    print("⏳ Waiting for PR to be merged... (checking every 20s)")
    while not gh.is_pr_merged(pr_url):
        time.sleep(20)
    print("✅ PR merged!")

    subprocess.run(
        ["git", "checkout", original_branch], check=True, capture_output=True
    )
    subprocess.run(
        ["git", "pull", "origin", original_branch], check=True, capture_output=True
    )

    tag_name = new_version
    tag_message = f"Version {new_version} [{tag_date_str}]"
    subprocess.run(["git", "tag", "-s", tag_name, "-m", tag_message], check=True)
    subprocess.run(["git", "push", "origin", tag_name], check=True)
    print(f"🏷️  Git tag '{tag_name}' created and pushed.")

    release_title = f"{new_version} [{changelog_date_str}]"

    if config["changelog_format"] == "md":
        release_body_md = "\n".join(latest_changelog_block.splitlines()[1:]).strip()
        release_body_md = demote_markdown_headings(release_body_md)
    else:
        release_body_rst = "\n".join(latest_changelog_block.splitlines()[2:]).strip()
        release_body_md = rst_to_markdown(release_body_rst)

    release_url = gh.create_release(tag_name, release_title, release_body_md)
    print(f"📦 Draft release created on GitHub: {release_url}")

    print("\n🎉 Release process completed successfully!")

    if is_bugfix:
        print("\n🐛 Bugfix release complete.")
        if questionary.confirm(
            "Do you want to create a PR to port the changelog to the main branch now?"
        ).ask():
            lines_to_skip = 2 if config["changelog_format"] != "md" else 1
            changelog_body_for_porting = "\n".join(
                latest_changelog_block.splitlines()[lines_to_skip:]
            ).strip()
            port_changelog_to_main(
                gh,
                config,
                new_version,
                changelog_body_for_porting,
                original_branch,
            )
        else:
            print("Skipping changelog port. Please remember to do it manually.")
