import os
import re
import subprocess
import sys
import tempfile


def run_git_cliff():
    """Runs the 'git cliff --unreleased' command and returns its output."""
    try:
        result = subprocess.run(
            ["git", "cliff", "--unreleased"], capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running 'git cliff': {e.stderr}", file=sys.stderr)
        sys.exit(1)


def process_changelog(changelog_text):
    """Processes raw changelog text to reorder and clean the Dependencies section."""
    lines = changelog_text.splitlines()

    # Iterate through the lines to find the start and end of the section
    # to isolate it for Dependency processing
    dep_start_index = -1
    dep_end_index = -1
    section_separator = ""

    for i, line in enumerate(lines):
        if line.strip() == "Dependencies":
            dep_start_index = i
            if i + 1 < len(lines):
                section_separator = lines[i + 1]
            continue

        # Dependencies section is over when we find the header for the next section
        if dep_start_index != -1 and i > dep_start_index + 1:
            stripped_line = line.strip()
            # Check if the line is a header section
            if (
                len(stripped_line) > 3
                and len(set(stripped_line)) == 1
                and stripped_line[0] in ["~", "+", "=", "-"]
            ):
                dep_end_index = i - 1
                break

    # If the file ends mid-section, mark the end right to the bottom
    if dep_start_index != -1 and dep_end_index == -1:
        dep_end_index = len(lines)

    # If no Dependencies section was found, just return
    if dep_start_index == -1:
        return changelog_text.strip()

    lines_before_deps = lines[:dep_start_index]
    dependency_lines = lines[dep_start_index + 2 : dep_end_index]
    lines_after_deps = lines[dep_end_index:]

    bumped_dependencies = {}
    other_dependencies = []

    # Regex to match dependency updates
    # 'Update [package] requirement from [old] to [new]'
    dep_update_pattern = re.compile(
        r"-\s*(?:Update|Bump)\s+`?`?([\w-]+)`?`?\s+requirement.*to\s+([~<>=!0-9a-zA-Z.,-]+)"
    )

    for line in dependency_lines:
        match = dep_update_pattern.search(line)
        if match:
            package_name = match.group(1)
            version_spec = match.group(2)
            final_version_spec = version_spec.split(",")[-1]
            bumped_dependencies[package_name] = (
                f"- Bumped ``{package_name}{final_version_spec}``"
            )
        else:
            if line.strip() and line not in other_dependencies:
                other_dependencies.append(line)

    final_lines = lines_before_deps
    final_lines.append(lines[dep_start_index])
    final_lines.append(section_separator)

    final_lines.extend(sorted(bumped_dependencies.values()))
    final_lines.extend(other_dependencies)

    # new line after Dependencies section
    if lines_after_deps:
        final_lines.append("")

    final_lines.extend(lines_after_deps)

    return "\n".join(final_lines)


def format_with_docstrfmt_file(content):
    """Formats content using a temporary file and exits if docstrfmt is missing or fails."""
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".rst") as tf:
            temp_file_path = tf.name
            tf.write(content)

        subprocess.run(
            [
                "docstrfmt",
                "--no-docstring-trailing-line",
                "--ignore-cache",
                "--line-length",
                "74",
                temp_file_path,
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        with open(temp_file_path, "r") as tf:
            formatted_content = tf.read()

        return formatted_content.strip()

    except subprocess.CalledProcessError as e:
        print("\nError running `docstrfmt` command", file=sys.stderr)
        print(f"{e.stderr}", file=sys.stderr)
        sys.exit(1)
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


def main():
    """Main function to execute the script."""
    raw_changelog = run_git_cliff()

    if raw_changelog:
        processed_changelog = process_changelog(raw_changelog)
        final_changelog = format_with_docstrfmt_file(processed_changelog)
        print(final_changelog)


if __name__ == "__main__":
    main()
