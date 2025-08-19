import os
import re
import sys
from ast import literal_eval

import questionary


def get_current_version(config):
    # Parses the VERSION tuple from the specified file.
    # Returns the version string (e.g., "1.2.0") or None if version_path is not set.
    version_path = config.get("version_path")
    if not version_path or not os.path.exists(version_path):
        # Return None if path is missing, allowing the main script to handle it
        return None, None

    with open(version_path, "r") as f:
        content = f.read()

    match = re.search(r"^VERSION\s*=\s*\((.+?)\)", content, re.MULTILINE)
    if not match:
        raise RuntimeError(f"Could not find the VERSION tuple in {version_path}.")

    try:
        version_parts = [part.strip() for part in match.group(1).split(",")]
        major, minor, patch, type = (
            version_parts[0],
            version_parts[1],
            version_parts[2],
            version_parts[3],
        )
        return f"{major}.{minor}.{patch}", literal_eval(type)
    except IndexError:
        raise RuntimeError(
            f"The VERSION tuple in {version_path} does not appear to have at least three elements."
        )


def bump_version(config, new_version):
    """Updates the VERSION tuple. Returns True on success, False if version_path is not configured."""
    version_path = config.get("version_path")
    if not version_path:
        # version bumping was not performed
        return False

    try:
        new_version_parts = new_version.split(".")
        if len(new_version_parts) != 3:
            raise ValueError("Version must be in the format X.Y.Z")
        new_major, new_minor, new_patch = new_version_parts
    except ValueError as e:
        print(f"Error: Invalid version format. {e}", file=sys.stderr)
        sys.exit(1)

    with open(version_path, "r") as f:
        content = f.read()

    new_tuple_string = f'({new_major}, {new_minor}, {new_patch}, "final")'

    # Replace the entire line containing the VERSION tuple
    new_content, count = re.subn(
        r"^VERSION\s*=\s*\(.*\)",
        f"VERSION = {new_tuple_string}",
        content,
        count=1,
        flags=re.MULTILINE,
    )

    if count == 0:
        raise RuntimeError(f"Failed to find and bump VERSION tuple in {version_path}.")

    with open(version_path, "w") as f:
        f.write(new_content)
    return True


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
