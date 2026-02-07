import re

from commitizen.cz.base import BaseCommitizen, ValidationResult

_TITLE_ISSUE_RE = re.compile(r"^[A-Z][^\n]* \#(\d+)$")


class OpenWispCommitizen(BaseCommitizen):
    """Commitizen plugin for OpenWISP commit conventions."""

    # Single source for allowed prefixes
    ALLOWED_PREFIXES = [
        "feature",
        "change",
        "fix",
        "docs",
        "test",
        "ci",
        "chores",
        "qa",
        "deps",
        "release",
        "bump",
    ]

    ERROR_TEMPLATE = (
        "Invalid commit message format\n\n"
        "Expected format:\n\n"
        "  [prefix] Capitalized title #<issue>\n\n"
        "  <long-description>\n\n"
        "  Fixes #<issue>\n\n"
        "Examples:\n\n"
        "  [feature] Add subnet import support #104\n\n"
        "  Add support for importing multiple subnets from a CSV file.\n\n"
        "  Fixes #104"
    )

    def _validate_title(self, value: str) -> bool | str:
        value = value.strip()
        if not value:
            return "Commit title cannot be empty."
        if not _TITLE_ISSUE_RE.match(value):
            return (
                "Commit title must start with a capital letter and "
                "end with an issue number (e.g. #104)."
            )
        return True

    def questions(self):
        return [
            {
                "type": "list",
                "name": "change_type",
                "message": "Select the type of change you are committing",
                "choices": [
                    {"value": prefix, "name": f"[{prefix}]"}
                    for prefix in self.ALLOWED_PREFIXES
                ],
            },
            {
                "type": "input",
                "name": "title",
                "message": "Commit title (short, first letter capital)",
                "validate": self._validate_title,
            },
            {
                "type": "input",
                "name": "how",
                "message": ("Describe what you changed and how it addresses the issue"),
                "validate": lambda v: (
                    True if v.strip() else "Commit body cannot be empty."
                ),
            },
        ]

    def message(self, answers):
        prefix_value = answers["change_type"]
        prefix = f"[{prefix_value}]"
        title = answers["title"].strip()
        body = answers["how"].strip()
        # Extract issue number from title
        match = _TITLE_ISSUE_RE.search(title)
        if not match:
            raise ValueError(
                "Commit title must end with an issue reference like #<issue_number>."
            )
        issue_number = match.group(1)
        return f"{prefix} {title}\n\n" f"{body}\n\n" f"Fixes #{issue_number}"

    def validate_commit_message(
        self,
        *,
        commit_msg: str,
        pattern: re.Pattern[str],
        allow_abort: bool,
        allowed_prefixes: list[str],
        max_msg_length: int | None,
        commit_hash: str,
    ) -> ValidationResult:
        """Validate commit message and return user-friendly errors."""
        if not commit_msg:
            return ValidationResult(
                allow_abort, [] if allow_abort else ["commit message is empty"]
            )
        # First check if it matches the pattern
        match_result = pattern.fullmatch(commit_msg)
        if not match_result:
            return ValidationResult(False, [self.ERROR_TEMPLATE])
        # Then verify it starts with an allowed prefix or is a merge commit
        # Use self.ALLOWED_PREFIXES for our custom prefixes
        # Allow compound prefixes like [tests:fix] as long as first part is allowed
        if commit_msg.startswith("Merge "):
            pass  # Merge commits are allowed
        elif not any(
            re.match(rf"\[{prefix}([!/:]|\])", commit_msg)
            for prefix in self.ALLOWED_PREFIXES
        ):
            return ValidationResult(False, [self.ERROR_TEMPLATE])
        # Check message length limit
        if max_msg_length is not None and max_msg_length > 0:
            msg_len = len(commit_msg.partition("\n")[0].strip())
            if msg_len > max_msg_length:
                return ValidationResult(
                    False,
                    [
                        f"commit message length exceeds the limit ({max_msg_length} chars)",
                    ],
                )
        return ValidationResult(True, [])

    def format_error_message(self, message: str) -> str:
        return self.ERROR_TEMPLATE

    def example(self) -> str:
        return (
            "[feature] Add commit convention enforcement #110\n\n"
            "Introduce a Commitizen-based commit workflow to standardize\n"
            "commit messages across the OpenWISP project.\n\n"
            "Fixes #110"
        )

    def schema(self) -> str:
        return "[<type>] <Title>"

    def schema_pattern(self) -> str:
        # Allow merge commits (starting with "Merge") or regular commits with prefix
        # Using \Z instead of $ to truly anchor to end-of-string
        # Split into two alternatives: merge commits and regular commits
        merge_pattern = r"Merge .*"
        # Regular commits: header with optional footer section
        # Footer section: blank line + optional body + "Fixes #<issue>"
        # Body is optional (.* allows empty) and there's no second blank line required
        regular_pattern = (
            r"\[[a-z0-9!/:-]+\] [A-Z][^\n]*( #(?P<issue>\d+))?"
            r"$(\n\n(.*\n)?(?:Close|Closes|Closed|Fix|Fixes|Fixed"
            r"|Resolve|Resolves|Resolved|Related to) #(?P=issue)\n?)?"
        )
        return rf"(?sm)^(?:{merge_pattern}|{regular_pattern})\Z"

    def info(self) -> str:
        prefixes_list = "\n".join(f"  - {prefix}" for prefix in self.ALLOWED_PREFIXES)
        return (
            "OpenWISP Commit Convention\n\n"
            "Commit messages must follow this structure:\n\n"
            "  [type] Capitalized title #<issue_number>\n\n"
            "  <description>\n\n"
            "  Fixes #<issue_number>\n\n"
            f"Allowed commit prefixes:\n\n{prefixes_list}\n\n"
            "If in doubt, use chores."
        )


__all__ = ["OpenWispCommitizen"]
