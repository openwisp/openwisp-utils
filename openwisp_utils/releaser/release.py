import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime

import pypandoc
import questionary
import requests
from openwisp_utils.releaser.config import load_config
from openwisp_utils.releaser.generate_changelog import (
    format_rst_block,
    process_changelog,
    run_git_cliff,
)
from openwisp_utils.releaser.github import GitHub
from openwisp_utils.releaser.version import bump_version, get_current_version

MAIN_BRANCHES = ["main", "master"]


def adjust_markdown_headings(markdown_text):
    """Adjusts heading levels for the CHANGES.md file (## -> ###, etc.)."""
    markdown_text = re.sub(
        r"(?m)^### (Other changes|Dependencies|Backward-incompatible changes)",
        r"#### \1",
        markdown_text,
    )
    markdown_text = re.sub(
        r"(?m)^## (Features|Changes|Bugfixes)", r"### \1", markdown_text
    )
    return markdown_text


def demote_markdown_headings(markdown_text):
    """Reduces heading levels for the GitHub release body"""
    markdown_text = re.sub(r"(?m)^### ", "# ", markdown_text)
    markdown_text = re.sub(r"(?m)^#### ", "## ", markdown_text)
    return markdown_text


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

    if config.get("repo"):
        checks.append((True, f"Repository '{config['repo']}' is found from origin."))
    else:
        checks.append(
            (
                False,
                "Repository was not found with git. Please set git remote repository on origin.",
            )
        )

    if token and config:
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


def get_gpt_summary(content, file_format, token):
    # Asks the user if they want to use GPT for summarizing the changelog,
    # and handles the interaction loop (Accept/Retry/Use Original).
    if not questionary.confirm(
        "Do you want to use an AI to generate a human-readable summary of the changelog?"
    ).ask():
        return content

    if not token:
        print(
            "⚠️ CHATGPT_TOKEN environment variable is not set. Skipping AI summary.",
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


def determine_new_version(current_version_str, current_type, is_bugfix):
    """Automatically determines the new version based on the current version and branch."""
    if not current_version_str:
        return questionary.text(
            "Could not determine the current version. Please enter the new version:"
        ).ask()

    major, minor, patch = map(int, current_version_str.split("."))

    if current_type != "final":
        # If the current version is not final, suggest the same version
        suggested_version = f"{major}.{minor}.{patch}"
    elif is_bugfix:
        # Bump patch for bugfix branches
        suggested_version = f"{major}.{minor}.{patch + 1}"
    else:
        # Bump minor for main branches
        suggested_version = f"{major}.{minor + 1}.0"

    print(f"\nSuggesting new version: {suggested_version}")
    use_suggested = questionary.confirm(
        "Do you want to use this version?", default=True
    ).ask()

    if use_suggested:
        return suggested_version
    else:
        return questionary.text("Please enter the desired version:").ask()


def get_current_branch():
    """Get the current Git branch name."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def rst_to_markdown(text):
    """Convert reStructuredText to Markdown using pypandoc."""
    escaped_text = re.sub(r"(?<!`)_", r"\\_", text)
    return pypandoc.convert_text(
        escaped_text, "gfm", format="rst", extra_args=["--wrap=none"]
    ).strip()


def format_file_with_docstrfmt(file_path):
    """Format a file using `docstrfmt`."""
    subprocess.run(
        ["docstrfmt", "--ignore-cache", "--line-length", "74", file_path],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    print(f"✅ Formatted {file_path} successfully.")


def get_release_block_from_file(changelog_path, version):
    """Reads the entire changelog file and extracts the block for a specific version."""
    with open(changelog_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    release_lines = []
    in_release_block = False
    is_md = changelog_path.endswith(".md")
    start_pattern = f"## Version {version}" if is_md else f"Version {version}"
    next_version_pattern = "## Version " if is_md else "Version "

    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith(start_pattern):
            in_release_block = True
            release_lines.append(line)
            continue
        if in_release_block and stripped_line.startswith(next_version_pattern):
            break
        if in_release_block:
            release_lines.append(line)

    return "".join(release_lines).strip() if release_lines else None


def update_changelog_file(changelog_path, new_block, is_port=False):
    # Updates the changelog file for all release types.
    # - For a feature release, it replaces the entire [Unreleased] section with the new content.
    # - For a ported bugfix, it inserts the new block after the [Unreleased] section.

    is_md = changelog_path.endswith(".md")
    try:
        with open(changelog_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        content = "# Change log\n\n" if is_md else "Changelog\n=========\n\n"

    # Regex to find the entire [Unreleased] block, from its header to the next version.
    unreleased_block_regex_str = (
        r"^(## Version \S+ \[Unreleased\](?:.|\n)*?)(?=\n## Version|\Z)"
        if is_md
        else r"^(Version \S+ \[Unreleased\]\n-+(?:.|\n)*?)(?=\n^Version|\Z)"
    )
    unreleased_block_regex = re.compile(
        unreleased_block_regex_str, re.IGNORECASE | re.MULTILINE
    )
    unreleased_match = unreleased_block_regex.search(content)

    if not unreleased_match:
        # Fallback if no [Unreleased] section is found: insert after the main title.
        lines = content.splitlines(keepends=True)
        header_end_index = 1
        if len(lines) > 1 and ("===" in lines[1] or "---" in lines[1]):
            header_end_index = 2
        while len(lines) > header_end_index and not lines[header_end_index].strip():
            header_end_index += 1
        lines.insert(header_end_index, new_block.strip() + "\n\n")
        new_content = "".join(lines)
    elif is_port:
        # For a bugfix port, insert the new block AFTER the [Unreleased] block.
        insertion_point = unreleased_match.end()
        new_content = (
            content[:insertion_point].rstrip()
            + "\n\n"
            + new_block.strip()
            + "\n"
            + content[insertion_point:]
        )
    else:
        # For a feature release, REPLACE the entire [Unreleased] block.
        # We add a newline to the replacement to ensure there's a blank line
        # between the new block and the next version.
        replacement = new_block.strip() + "\n"
        new_content = unreleased_block_regex.sub(replacement, content, count=1)

    # Clean up any triple newlines to ensure clean formatting
    final_content = re.sub(r"\n\n\n+", "\n\n", new_content.strip()) + "\n"

    with open(changelog_path, "w", encoding="utf-8") as f:
        f.write(final_content)


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
    try:
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
            "for version {new_version} on branch '{original_branch}'..."
        )

        raw_changelog_block = run_git_cliff(new_version)
        raw_changelog_block = raw_changelog_block.replace("#REPO#", config["repo"])
        if not raw_changelog_block:
            print("No changes found for the new release. Exiting.")
            sys.exit(0)

        processed_block = process_changelog(raw_changelog_block)

        print("\n📝  Generated and Formatted Changelog Block:\n")
        formatted_block_rst = format_rst_block(processed_block)

        gpt_token = os.environ.get("CHATGPT_TOKEN")
        final_formatted_block = get_gpt_summary(
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
        latest_changelog_block = get_release_block_from_file(
            changelog_path, new_version
        )
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
            release_body_rst = "\n".join(
                latest_changelog_block.splitlines()[2:]
            ).strip()
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

    except KeyboardInterrupt:
        print("\n\n❌ Release process terminated by user.")
        sys.exit(1)
    except (
        subprocess.CalledProcessError,
        requests.RequestException,
        RuntimeError,
        FileNotFoundError,
    ) as e:
        print(f"\n❌ An error occurred: {e}", file=sys.stderr)
        if isinstance(e, subprocess.CalledProcessError):
            print(f"Error Details: {e.stderr}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
