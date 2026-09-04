import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime

import questionary
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
    AbortSignal,
    SkipSignal,
    adjust_markdown_headings,
    branch_exists,
    demote_markdown_headings,
    format_file_with_docstrfmt,
    get_current_branch,
    get_remote_branch_commit,
    rst_to_markdown,
    run_git,
)
from openwisp_utils.releaser.version import (
    bump_version,
    determine_new_version,
    get_current_version,
    supports_prerelease,
)

MAIN_BRANCHES = ["master", "main"]


def wait_for_pr_merge(gh, pr_url):
    """Waits for a release pull request and returns its merged metadata."""
    print("⏳ Waiting for PR to be merged... (checking every 20s)")
    while True:
        pull_request = gh.get_pr(pr_url)
        if pull_request.get("merged"):
            print("✅ PR merged!")
            return pull_request
        if pull_request.get("state") == "closed":
            raise RuntimeError(
                "The release pull request was closed without being merged. "
                "Reopen or replace it before resuming the release."
            )
        time.sleep(20)


def get_release_version(pull_request):
    """Returns the version encoded in a release pull request branch."""
    branch = pull_request.get("head", {}).get("ref", "")
    if not branch.startswith("release/") or not branch.removeprefix("release/"):
        raise RuntimeError(
            "The pull request must originate from a release/<version> branch."
        )
    return branch.removeprefix("release/")


def tag_exists_on_branch(tag_name, branch):
    """Checks whether a tag resolves to a commit contained by a branch."""
    tag = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{tag_name}^{{commit}}"],
        capture_output=True,
        text=True,
    )
    if tag.returncode:
        return False
    return (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", f"{tag_name}^{{commit}}", branch],
            capture_output=True,
            text=True,
        ).returncode
        == 0
    )


def complete_release_artifacts(
    gh,
    config,
    version,
    base_branch,
    latest_changelog_block,
    tag_date_str,
    changelog_date_str,
):
    """Creates only the release artifacts that do not already exist."""
    run_git(["checkout", base_branch], f"checkout '{base_branch}'")
    run_git(["pull", "origin", base_branch], f"pull '{base_branch}'")
    run_git(["fetch", "origin", "--tags"], "fetch remote tags")

    tag_name = version
    if tag_exists_on_branch(tag_name, base_branch):
        print(f"🏷️  Git tag '{tag_name}' already exists on '{base_branch}'.")
    else:
        local_tag = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{tag_name}^{{commit}}"],
            capture_output=True,
            text=True,
        )
        if local_tag.returncode == 0:
            raise RuntimeError(
                f"Git tag '{tag_name}' exists but is not contained by '{base_branch}'."
            )
        tag_message = f"Version {version} [{tag_date_str}]"
        run_git(["tag", "-s", tag_name, "-m", tag_message], f"create tag '{tag_name}'")
        run_git(["push", "origin", tag_name], f"push tag '{tag_name}'")
        print(f"🏷️  Git tag '{tag_name}' created and pushed.")

    release_title = f"{version} [{changelog_date_str}]"
    if config["changelog_format"] == "md":
        release_body_md = "\n".join(latest_changelog_block.splitlines()[1:]).strip()
        release_body_md = demote_markdown_headings(release_body_md)
    else:
        release_body_rst = "\n".join(latest_changelog_block.splitlines()[2:]).strip()
        release_body_md = rst_to_markdown(release_body_rst)

    existing_release = gh.get_release(tag_name)
    if existing_release:
        print(f"📦 GitHub release already exists: {existing_release['html_url']}")
    else:
        try:
            release_url = gh.create_release(tag_name, release_title, release_body_md)
            print(f"📦 Draft release created on GitHub: {release_url}")
        except SkipSignal:
            print(
                "\nOperation skipped. Please create the GitHub release manually."
                f"\n  Tag: {tag_name}"
                f"\n  Title: {release_title}"
                "\n  Body: (You can find the content in the latest commit)."
            )
            questionary.confirm(
                "Press Enter when you have created the release manually."
            ).ask()


def resume(pr_url):
    """Completes a release after its already-created pull request is merged."""
    config, gh = check_prerequisites()
    pull_request = wait_for_pr_merge(gh, pr_url)
    version = get_release_version(pull_request)
    base_branch = pull_request["base"]["ref"]

    run_git(["checkout", base_branch], f"checkout '{base_branch}'")
    run_git(["pull", "origin", base_branch], f"pull '{base_branch}'")
    latest_changelog_block = get_release_block_from_file(config, version)
    if not latest_changelog_block:
        raise RuntimeError(
            f"Could not find the changelog entry for version {version} on '{base_branch}'."
        )

    changelog_date = datetime.now().strftime("%Y-%m-%d")
    header = latest_changelog_block.splitlines()[0]
    date_match = re.search(r"\[(\d{4}-\d{2}-\d{2})\]", header)
    if date_match:
        changelog_date = date_match.group(1)
    complete_release_artifacts(
        gh,
        config,
        version,
        base_branch,
        latest_changelog_block,
        datetime.now().strftime("%d-%m-%Y"),
        changelog_date,
    )
    _complete_follow_up(gh, config, version, latest_changelog_block, base_branch)


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
        has_permission, reason = gh.check_pr_creation_permission()
        if has_permission:
            checks.append(
                (True, f"GitHub token has access to the '{config['repo']}' repository.")
            )
        else:
            checks.append((False, reason))

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


def resolve_main_branch(question):
    """Returns the local main branch, asking the user when both exist."""
    master_exists = branch_exists("master")
    main_exists = branch_exists("main")
    if master_exists and main_exists:
        return questionary.select(question, choices=MAIN_BRANCHES).ask()
    if master_exists:
        return "master"
    if main_exists:
        return "main"
    print("Neither 'master' nor 'main' branches were found locally.")
    return None


def port_changelog_to_main(gh, config, version, changelog_body, original_branch):
    """Checks out the main branch, updates the changelog, and creates a new PR."""
    print("\n" + "=" * 50)
    print("🤖 Starting Changelog Porting Process")
    print("=" * 50)

    is_md = config["changelog_path"].endswith(".md")
    changelog_date_str = datetime.now().strftime("%Y-%m-%d")
    prefix = "Version " if config.get("changelog_uses_version_prefix", True) else ""

    if is_md:
        version_header = f"## {prefix}{version} [{changelog_date_str}]"
        # The body has already been adjusted for the file, so no heading changes are needed.
        full_block_to_port = f"{version_header}\n\n{changelog_body}"
    else:  # rst
        version_header = f"{prefix}{version} [{changelog_date_str}]"
        underline = "-" * len(version_header)
        full_block_to_port = f"{version_header}\n{underline}\n\n{changelog_body}"

    try:
        main_branch = resolve_main_branch(
            "Which branch should the changelog be ported to?"
        )

        if not main_branch:
            print("Skipping changelog porting.")
            return

        port_branch = f"chore/port-changelog-{version}"
        commit_message = f"[docs] Port changelog for {version}"
        pr_title = f"[docs] Port changelog for release {version}"
        existing_pr = gh.find_pr(port_branch, main_branch, pr_title)
        if isinstance(existing_pr, dict):
            print(
                f"Changelog port pull request already exists: {existing_pr['html_url']}"
            )
            return

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
            ["git", "push", "-u", "origin", port_branch],
            check=True,
            capture_output=True,
        )

        print("Creating pull request...")
        try:
            pr_url = gh.create_pr(port_branch, main_branch, pr_title)
            print(
                f"\n✅ Successfully created Pull Request for changelog port: {pr_url}"
            )
        except SkipSignal:
            print(
                "\nOperation skipped. Please create the PR manually."
                f"\n  Branch: {port_branch}"
                f"\n  Base: {main_branch}"
                f"\n  Title: {pr_title}"
            )
            questionary.confirm(
                "Press Enter when you have created the PR manually."
            ).ask()

    finally:
        print(f"\nSwitching back to original branch '{original_branch}'...")
        subprocess.run(
            ["git", "checkout", original_branch], check=True, capture_output=True
        )


def bump_to_next_alpha(gh, config, released_version, original_branch):
    """Bumps the version to the next alpha release and opens a PR for it."""
    print("\n" + "=" * 50)
    print("🤖 Starting Version Bump to the Next Alpha Release")
    print("=" * 50)
    package_type = config.get("package_type")
    if not supports_prerelease(package_type):
        print(
            f"Skipping alpha version bump: '{package_type}' projects cannot store "
            "an alpha marker."
        )
        return
    next_version = determine_new_version(released_version, "final", is_bugfix=False)
    if not next_version:
        print("No version provided. Version bump cancelled.")
        return

    base_branch = resolve_main_branch("Which branch should the version be bumped on?")
    if not base_branch:
        print("Skipping the version bump.")
        return
    bump_branch = f"chore/bump-version-{next_version}"
    pr_title = f"[bump] Bumped version to {next_version} alpha"
    force_with_lease = None
    bump_branch_created = False
    changes_committed = False

    existing_pr = gh.find_pr(bump_branch, base_branch, pr_title)
    if isinstance(existing_pr, dict):
        print(f"Version bump pull request already exists: {existing_pr['html_url']}")
        return

    try:
        print(f"Checking out '{base_branch}' and pulling latest changes...")
        run_git(["checkout", base_branch], f"checkout '{base_branch}'")
        run_git(["pull", "origin", base_branch], f"pull '{base_branch}'")
        while True:
            remote_commit = get_remote_branch_commit(bump_branch)
            if not branch_exists(bump_branch) and not remote_commit:
                break
            decision = questionary.select(
                f"Branch '{bump_branch}' already exists. How would you like to proceed?",
                choices=[
                    f"Reset it to '{base_branch}'",
                    "Use a different branch name",
                    "Abort the version bump",
                ],
            ).ask()
            if decision == f"Reset it to '{base_branch}'":
                force_with_lease = remote_commit
                break
            elif decision == "Use a different branch name":
                bump_branch = questionary.text("Enter the branch name:").ask()
                if not bump_branch:
                    raise AbortSignal("No branch name provided.")
            else:  # Abort or None
                raise AbortSignal("User aborted the version bump.")
        print(f"Creating new branch '{bump_branch}'...")
        run_git(["checkout", "-B", bump_branch], f"create branch '{bump_branch}'")
        bump_branch_created = True
        was_bumped = bump_version(config, next_version, version_type="alpha")
        if was_bumped:
            print(f"✅ Version bumped to {next_version} and set to 'alpha'.")
        else:
            print(
                "\n⚠️  The version number could not be bumped automatically."
                "\n   Please bump it manually before the changelog is committed."
            )
            questionary.confirm(
                "Press Enter when you have bumped the version number..."
            ).ask()
        changelog_path = config["changelog_path"]
        prefix = "Version " if config.get("changelog_uses_version_prefix", True) else ""
        version_header = f"{prefix}{next_version} [unreleased]"
        if config["changelog_format"] == "md":
            unreleased_block = f"## {version_header}\n\nWork in progress."
        else:  # rst
            underline = "-" * len(version_header)
            unreleased_block = f"{version_header}\n{underline}\n\nWork in progress."

        update_changelog_file(changelog_path, unreleased_block)
        if config["changelog_format"] == "rst":
            format_file_with_docstrfmt(changelog_path)
        print(f"✅ {changelog_path} has been updated.")
        print("Committing changes...")
        run_git(["add", "-u"], "stage the version bump")
        run_git(["commit", "-m", pr_title], "commit the version bump")
        changes_committed = True

        print(f"⤴️  Pushing branch '{bump_branch}' to origin...")
        push_args = ["push", "-u", "origin", bump_branch]
        if force_with_lease:
            push_args.insert(
                1,
                f"--force-with-lease=refs/heads/{bump_branch}:{force_with_lease}",
            )
        run_git(push_args, f"push branch '{bump_branch}'")
        print("Creating pull request...")
        pr_url = gh.create_pr(bump_branch, base_branch, pr_title)
        print(f"\n✅ Successfully created Pull Request for the version bump: {pr_url}")
    except (SkipSignal, AbortSignal) as e:
        print(
            f"\n⚠️  {e}"
            "\nPlease complete the version bump manually."
            f"\n  Branch: {bump_branch}"
            f"\n  Base: {base_branch}"
            f"\n  Title: {pr_title}"
        )
    finally:
        if not bump_branch_created or changes_committed:
            print(f"\nSwitching back to original branch '{original_branch}'...")
            subprocess.run(
                ["git", "checkout", original_branch], check=True, capture_output=True
            )
        else:
            print(
                f"\nKeeping branch '{bump_branch}' checked out because it has "
                "uncommitted version-bump changes."
            )


def _complete_follow_up(gh, config, version, latest_changelog_block, base_branch):
    """Offers the existing post-release follow-up appropriate for the base branch."""
    is_bugfix = base_branch not in MAIN_BRANCHES
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
                gh, config, version, changelog_body_for_porting, base_branch
            )
        else:
            print("Skipping changelog port. Please remember to do it manually.")
    elif (
        supports_prerelease(config.get("package_type"))
        and questionary.confirm(
            "Do you want to bump the version to the next alpha release now?"
        ).ask()
    ):
        bump_to_next_alpha(gh, config, version, base_branch)
    elif supports_prerelease(config.get("package_type")):
        print("Skipping the version bump. Please remember to do it manually.")
    else:
        print(
            f"Skipping alpha version bump: '{config.get('package_type')}' projects "
            "cannot store an alpha marker."
        )


def main(resume_pr_url=None):
    if resume_pr_url:
        resume(resume_pr_url)
        return
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

    processed_block = process_changelog(
        raw_changelog_block, changelog_format=config["changelog_format"]
    )
    formatted_block_rst = format_rst_block(processed_block)

    changelog_content = formatted_block_rst

    # Strip any header
    header_stripping_regex = re.compile(
        r"^(?:Version\s+)?\d+\.\d+\.\d+.*?\n[-~=]{3,}\n*", re.MULTILINE
    )
    changelog_body = header_stripping_regex.sub("", changelog_content).strip()

    changelog_date_str = datetime.now().strftime("%Y-%m-%d")
    tag_date_str = datetime.now().strftime("%d-%m-%Y")
    changelog_path = config["changelog_path"]
    prefix = "Version " if config.get("changelog_uses_version_prefix", True) else ""
    full_release_block = ""

    if config["changelog_format"] == "md":
        md_body = rst_to_markdown(changelog_body)
        md_body = adjust_markdown_headings(md_body)
        md_body = (
            md_body.replace("\\#", "#")
            .replace("\\[", "[")
            .replace("\\]", "]")
            .replace("# Version", "## Version")
        )
        version_header = f"## {prefix}{new_version} [{changelog_date_str}]"
        full_release_block = f"{version_header}\n\n{md_body}"
    else:  # rst
        version_header = f"{prefix}{new_version} [{changelog_date_str}]"
        underline = "-" * len(version_header)
        full_release_block = f"{version_header}\n{underline}\n\n{changelog_body}"

    print("\n📝 The following block will be added to the changelog:\n")
    print(full_release_block)

    if not questionary.confirm("Accept this block and proceed?").ask():
        print("Release cancelled.")
        sys.exit(0)

    # Now we write the approved block to the file.
    update_changelog_file(changelog_path, full_release_block)

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
    latest_changelog_block = get_release_block_from_file(config, new_version)
    if not latest_changelog_block:
        print(
            "\nWarning: Could not re-read the changelog block. Using initially generated content.",
            file=sys.stderr,
        )
        latest_changelog_block = full_release_block

    if config["changelog_format"] == "rst":
        format_file_with_docstrfmt(changelog_path)

    release_branch = f"release/{new_version}"
    pr_title = f"[release] Version {new_version}"
    subprocess.run(
        ["git", "checkout", "-b", release_branch], check=True, capture_output=True
    )

    paths_to_add = [changelog_path]
    if version_path := config.get("version_path"):
        paths_to_add.append(version_path)
    print("Adding release changes to git...")
    subprocess.run(["git", "add", *paths_to_add], check=True, capture_output=True)

    commit_message = f"[release] Version {new_version}"
    subprocess.run(
        ["git", "commit", "-m", commit_message], check=True, capture_output=True
    )
    print("✅ Changes committed to the release branch.")

    print(f"⤴️  Pushing new branch '{release_branch}' to GitHub...")
    subprocess.run(
        ["git", "push", "-u", "origin", release_branch],
        check=True,
        capture_output=True,
    )

    try:
        pr_url = gh.create_pr(release_branch, original_branch, pr_title)
        print(f"✅ Pull Request created: {pr_url}")

        print("⏳ Waiting for PR to be merged... (checking every 20s)")
        while not gh.is_pr_merged(pr_url):
            time.sleep(20)
        print("✅ PR merged!")

    except SkipSignal:
        print(
            "\nOperation skipped. Please create and merge the PR manually."
            f"\n  Branch: {release_branch}"
            f"\n  Base: {original_branch}"
            f"\n  Title: {pr_title}"
        )
        questionary.confirm("Press Enter when you have merged the PR manually.").ask()

    complete_release_artifacts(
        gh,
        config,
        new_version,
        original_branch,
        latest_changelog_block,
        tag_date_str,
        changelog_date_str,
    )

    print("\n🎉 Release process completed successfully!")

    _complete_follow_up(
        gh, config, new_version, latest_changelog_block, original_branch
    )
