import os
import re
import sys
from ast import literal_eval

import questionary


def get_current_version(config):
    # Parses the CURRENT_VERSION which comes from the version_path file 
    # Returns the version string (e.g., "1.2.0") or None if CURRENT_VERSION is not set.
    current_version = config.get("CURRENT_VERSION")
    if not current_version:
        # Return None if CURRENT_VERSION is missing, allowing the main script to handle it
        return None, None

    try:
        major, minor, patch = (
            current_version[0],
            current_version[1],
            current_version[2],
        )
        type = current_version[3] if len(current_version) > 3 else "final"
        return f"{major}.{minor}.{patch}", type
    except IndexError:
        raise RuntimeError(
            f"The VERSION tuple {current_version} does not appear to have at least three elements."
        )


def bump_version(config, new_version):
    """Updates the VERSION tuple. Returns True on success, False if version_path is not configured."""
    version_path = config.get("version_path")
    package_type = config.get("package_type")
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

    if package_type == "python":
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
    
    elif package_type == "npm":
        import json
        data = json.loads(content)
        data["version"] = new_version
        new_content = json.dumps(data, indent=2) + "\n"
        count = 1
    
    elif package_type == "docker":
        new_content, count = re.subn(
            r"^OPENWISP_VERSION\s*=\s*[^\s]+",
            f"OPENWISP_VERSION = {new_version}",
            content,
            count=1,
            flags=re.MULTILINE,
        )
        if count == 0:
            raise RuntimeError(f"Failed to find and bump OPENWISP_VERSION in {version_path}.")
    
    elif package_type == "ansible":
        new_content, count = re.subn(
            r'^__openwisp_version__\s*=\s*["\']([^"\']+)["\']',
            f'__openwisp_version__ = "{new_version}"',
            content,
            count=1,
            flags=re.MULTILINE,
        )
        if count == 0:
            raise RuntimeError(f"Failed to find and bump __openwisp_version__ in {version_path}.")
    
    elif package_type == "openwrt-agents":
        new_content = f"{new_version}\n"
        count = 1
        if count == 0:
            raise RuntimeError(f"Failed to find and bump in {version_path}")
    
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
