import ast
import os
import re
import subprocess


def get_package_name_from_setup():
    """Parses setup.py to find the package name without raising an error."""
    if not os.path.exists("setup.py"):
        return None

    with open("setup.py", "r") as f:
        content = f.read()
        match = re.search(r"name\s*=\s*['\"]([^'\"]+)['\"]", content)
        if match:
            return match.group(1)
    return None


def detect_changelog_style(changelog_path):
    # Detects if the changelog uses the 'Version ' prefix for its entries
    if not os.path.exists(changelog_path):
        return True
    with open(changelog_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Look for a line that starts with 'Version X.Y.Z'
    if re.search(r"^Version\s+\d+\.\d+\.\d+", content, re.MULTILINE):
        return True
    # Look for a line that starts with just 'X.Y.Z'
    if re.search(r"^\d+\.\d+\.\d+", content, re.MULTILINE):
        return False
    # Default to True if no version entries are found yet
    return True


def load_config():
    """Loads configuration from project files and git."""
    config = {}

    try:
        origin_url = (
            subprocess.check_output(["git", "remote", "get-url", "origin"])
            .decode("utf-8")
            .strip()
        )
        repo_path = origin_url.removesuffix(".git").rstrip("/")
        # SSH URLs
        if repo_path.startswith("git@"):
            config["repo"] = repo_path.split(":")[-1]
        # HTTPS URLs
        else:
            config["repo"] = "/".join(repo_path.split("/")[-2:])
    except (subprocess.CalledProcessError, FileNotFoundError):
        config["repo"] = None

    config["version_path"] = None
    config["CURRENT_VERSION"] = None

    project_name = get_package_name_from_setup()
    if project_name:
        package_directory = project_name.replace("-", "_")
        init_py_path = os.path.join(package_directory, "__init__.py")

        if os.path.exists(init_py_path):
            with open(init_py_path, "r") as f:
                content = f.read()
                version_match = re.search(r"^VERSION\s*=\s*\((.*)\)", content, re.M)
                if version_match:
                    config["version_path"] = init_py_path
                    try:
                        version_tuple = ast.literal_eval(f"({version_match.group(1)})")
                        config["CURRENT_VERSION"] = list(version_tuple)
                    except (ValueError, SyntaxError):
                        config["CURRENT_VERSION"] = None

    possible_changelog_names = [
        "CHANGES.rst",
        "CHANGELOG.rst",
        "CHANGES.md",
        "CHANGELOG.md",
    ]
    found_changelog = None
    for name in possible_changelog_names:
        if os.path.exists(name):
            found_changelog = name
            break

    if found_changelog:
        config["changelog_path"] = found_changelog
        config["changelog_format"] = "md" if found_changelog.endswith(".md") else "rst"
    else:
        raise FileNotFoundError(
            "Error: Changelog file is required. Could not find CHANGES.rst, "
            "CHANGELOG.rst, CHANGES.md, or CHANGELOG.md."
        )

    config["changelog_uses_version_prefix"] = detect_changelog_style(
        config["changelog_path"]
    )

    return config
