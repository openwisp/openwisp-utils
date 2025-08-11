import os
import re
import subprocess
import sys
import time
from datetime import datetime

import pypandoc
import questionary
import requests

from releaser.config import load_config
from releaser.generate_changelog import (
    format_rst_block,
    process_changelog,
    run_git_cliff,
)
from releaser.github import GitHub
from releaser.version import bump_version, get_current_version

MAIN_BRANCHES = ["main", "master"]


def get_current_branch():
    """Get the current Git branch name."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def rst_to_markdown(text):
    """Convert reStructuredText to Markdown using pypandoc."""
    try:
        return pypandoc.convert_text(text, "gfm", format="rst")
    except OSError:
        print("Error: `pandoc` is not installed. Please install it.", file=sys.stderr)
        sys.exit(1)


def format_file_with_docstrfmt(file_path):
    """Format a file using `docstrfmt`."""
    try:
        subprocess.run(
            ["docstrfmt", "--ignore-cache", "--line-length", "74", file_path],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"✅ Formatted {file_path} successfully.")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(
            f"\nWarning: Could not format {file_path} with `docstrfmt`.",
            file=sys.stderr,
        )
        if isinstance(e, subprocess.CalledProcessError):
            print(f"{e.stderr}", file=sys.stderr)


def update_changelog_file(changelog_path, final_release_block, new_version, is_bugfix):
    """Update the changelog file with the new release block."""
    try:
        with open(changelog_path, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = ["Changelog\n", "=========\n\n"]

    header_end_index = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("==="):
            header_end_index = i + 1
            break

    header_lines = lines[:header_end_index]
    body_lines = lines[header_end_index:]

    if not is_bugfix:
        history_start_index = -1
        for i, line in enumerate(body_lines):
            if line.strip().startswith("Version") and "[Unreleased]" not in line:
                history_start_index = i
                break

        historical_lines = (
            body_lines[history_start_index:] if history_start_index != -1 else []
        )

        major, minor, _ = new_version.split(".")
        next_unreleased_version = f"{major}.{int(minor) + 1}.0"
        new_unreleased_block = (
            f"\nVersion {next_unreleased_version} [Unreleased]\n"
            "--------------------------\n\n"
            "Work in progress.\n\n"
        )

        new_content = (
            "".join(header_lines)
            + new_unreleased_block
            + final_release_block
            + "\n\n"
            + "".join(historical_lines)
        )
    else:
        insertion_index = -1
        for i, line in enumerate(body_lines):
            if "Work in progress." in line:
                insertion_index = i + 1
                break

        if insertion_index == -1:
            raise RuntimeError(
                "Could not find 'Work in progress.' to insert bugfix release."
            )

        new_body_lines = (
            body_lines[:insertion_index]
            + ["\n"]
            + [final_release_block + "\n\n"]
            + body_lines[insertion_index:]
        )
        new_content = "".join(header_lines) + "".join(new_body_lines)

    with open(changelog_path, "w") as f:
        f.write(new_content)


def port_changelog_to_main(gh, config, version, changelog_block, original_branch):
    """Checks out the main branch, updates the changelog, and creates a new PR."""
    print("\n" + "=" * 50)
    print("🤖 Starting Changelog Porting Process")
    print("=" * 50)

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
            config["changelog_path"], changelog_block, version, is_bugfix=True
        )

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
    original_branch = get_current_branch()
    try:
        config = load_config()
        gh = GitHub(os.environ["GITHUB_TOKEN"], repo=config["repo"])
        is_bugfix = original_branch not in MAIN_BRANCHES
        release_type = "Bugfix" if is_bugfix else "Feature"

        print(
            f"🚀 Starting {release_type} Release Flow on branch '{original_branch}'..."
        )

        raw_changelog_block = run_git_cliff()
        if not raw_changelog_block:
            print("No changes found for the new release. Exiting.")
            sys.exit(0)

        processed_block = process_changelog(raw_changelog_block)

        print("\nPre-formatting the generated changelog block...")
        formatted_block = format_rst_block(processed_block)
        print("\n📝 Generated and Formatted Changelog Block:\n")
        print(formatted_block)

        if not questionary.confirm("Accept this block and proceed?").ask():
            print("Release cancelled.")
            sys.exit(0)

        current_version = get_current_version(config)
        new_version = questionary.text(
            f"Current version is {current_version}. Enter new version:"
        ).ask()

        if (
            new_version
            and questionary.confirm(f"Proceed with version {new_version}?").ask()
        ):
            changelog_date_str = datetime.now().strftime("%Y-%m-%d")
            tag_date_str = datetime.now().strftime("%d-%m-%Y")

            version_header = f"Version {new_version}  [{changelog_date_str}]"
            underline = "-" * len(version_header)

            final_release_block = re.sub(
                r"\[unreleased\]\n[=\-~+']+",
                f"{version_header}\n{underline}",
                formatted_block,
            )

            changelog_path = config["changelog_path"]
            update_changelog_file(
                changelog_path, final_release_block, new_version, is_bugfix
            )
            print(f"✅ {changelog_path} has been updated.")

            bump_version(config, new_version)
            print(f"✅ Version bumped to {new_version} and set to 'final'.")

            print(
                f"\n✋ Please review the updated '{changelog_path}' and make any final edits."
            )
            questionary.confirm("Press Enter when you have finished editing...").ask()

            print("\nRe-formatting the final changelog file...")
            format_file_with_docstrfmt(changelog_path)

            release_branch = f"release/{new_version}"
            pr_title = f"[release] Version {new_version}"
            subprocess.run(
                ["git", "checkout", "-b", release_branch],
                check=True,
                capture_output=True,
            )

            files_to_add = [config["version_path"], changelog_path]
            subprocess.run(
                ["git", "add"] + files_to_add, check=True, capture_output=True
            )

            commit_message = f"[release] Prepare for release {new_version}"
            subprocess.run(
                ["git", "commit", "-m", commit_message], check=True, capture_output=True
            )
            print("✅ Changes committed to the release branch.")

            print(f"⬆️ Pushing new branch '{release_branch}' to GitHub...")
            subprocess.run(
                ["git", "push", "origin", release_branch],
                check=True,
                capture_output=True,
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
                ["git", "pull", "origin", original_branch],
                check=True,
                capture_output=True,
            )

            tag_name = new_version
            tag_message = f"Version {new_version} [{tag_date_str}]"
            subprocess.run(
                ["git", "tag", "-s", tag_name, "-m", tag_message], check=True
            )
            subprocess.run(["git", "push", "origin", tag_name], check=True)
            print(f"🖋️ Git tag '{tag_name}' created and pushed.")

            release_body_md = rst_to_markdown(final_release_block)
            release_url = gh.create_release(tag_name, release_body_md)
            print(f"📦 Draft release created on GitHub: {release_url}")

            print("\n🎉 Release process completed successfully!")

            if is_bugfix:
                print("\n🐞 Bugfix release complete.")
                if questionary.confirm(
                    "Do you want to create a PR to port the changelog to the main branch now?"
                ).ask():
                    port_changelog_to_main(
                        gh, config, new_version, final_release_block, original_branch
                    )
                else:
                    print("Skipping changelog port. Please remember to do it manually.")

        else:
            print("Release cancelled.")
            sys.exit(0)

    except (
        subprocess.CalledProcessError,
        requests.RequestException,
        KeyError,
        RuntimeError,
        FileNotFoundError,
    ) as e:
        print(f"\n❌ An error occurred: {e}", file=sys.stderr)
        if isinstance(e, subprocess.CalledProcessError):
            print(f"Error Details: {e.stderr}", file=sys.stderr)
        if isinstance(e, KeyError) and "GITHUB_TOKEN" in str(e):
            print(
                "Please ensure the GITHUB_TOKEN environment variable is set.",
                file=sys.stderr,
            )
        sys.exit(1)


if __name__ == "__main__":
    main()
