import os
import re
import sys


def get_current_version(config):
    """Parses the VERSION tuple from the specified file and returns a string like "1.2.0"."""
    version_path = config.get("version_path")
    if not version_path or not os.path.exists(version_path):
        print(
            f"Error: version_path '{version_path}' in releaser.toml is invalid.",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(version_path, "r") as f:
        content = f.read()

    match = re.search(r"^VERSION\s*=\s*\((.+?)\)", content, re.MULTILINE)
    if not match:
        raise RuntimeError(f"Could not find the VERSION tuple in {version_path}.")

    try:
        version_parts = [part.strip() for part in match.group(1).split(",")]
        major, minor, patch = version_parts[0], version_parts[1], version_parts[2]
        return f"{major}.{minor}.{patch}"
    except IndexError:
        raise RuntimeError(
            f"The VERSION tuple in {version_path} does not appear to have at least three elements."
        )


def bump_version(config, new_version):
    """Updates the VERSION tuple in the specified file, setting the release status to 'final'."""
    version_path = config["version_path"]
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
