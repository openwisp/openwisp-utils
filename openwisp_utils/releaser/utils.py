import re
import subprocess

import pypandoc


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
