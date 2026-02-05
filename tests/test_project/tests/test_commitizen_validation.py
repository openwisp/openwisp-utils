import pytest
from commitizen.config import BaseConfig


def valid_commit(issue="110"):
    return (
        f"[feature] Add subnet import support #{issue}\n\n"
        "Add support for importing multiple subnets from a CSV file.\n\n"
        f"Fixes #{issue}"
    )


@pytest.fixture
def cz():
    # Import inside fixture to avoid circular import during pytest collection
    from openwisp_utils.commitizen.openwisp import OpenWispCommitizen

    return OpenWispCommitizen(BaseConfig())


def test_valid_commit_message(cz):
    assert cz.validate_commit_message(valid_commit()) is True


def test_empty_commit_message(cz):
    assert cz.validate_commit_message("") is False


def test_missing_issue_in_title(cz):
    message = "[feature] Add subnet import support\n\n" "Some body\n\n" "Fixes #104"
    assert cz.validate_commit_message(message) is False


def test_issue_not_at_end_of_title(cz):
    message = (
        "[feature] Add #104 subnet import support\n\n" "Some body\n\n" "Fixes #104"
    )
    assert cz.validate_commit_message(message) is False


def test_title_not_capitalized(cz):
    message = (
        "[feature] add subnet import support #104\n\n" "Some body\n\n" "Fixes #104"
    )
    assert cz.validate_commit_message(message) is False


def test_missing_blank_line_after_header(cz):
    message = "[feature] Add subnet import support #104\n" "Some body\n\n" "Fixes #104"
    assert cz.validate_commit_message(message) is False


def test_missing_body(cz):
    message = "[feature] Add subnet import support #104\n\n" "Fixes #104"
    assert cz.validate_commit_message(message) is False


def test_missing_fixes_footer(cz):
    message = "[feature] Add subnet import support #104\n\n" "Some body"
    assert cz.validate_commit_message(message) is False


def test_missing_blank_line_before_footer(cz):
    message = "[feature] Add subnet import support #104\n\n" "Some body\n" "Fixes #104"
    assert cz.validate_commit_message(message) is False


def test_fixes_footer_not_last_line(cz):
    message = (
        "[feature] Add subnet import support #104\n\n"
        "Some body\n\n"
        "Fixes #104\n"
        "Extra line"
    )
    assert cz.validate_commit_message(message) is False


def test_mismatched_issue_numbers(cz):
    message = (
        "[feature] Add subnet import support #104\n\n" "Some body\n\n" "Fixes #105"
    )
    assert cz.validate_commit_message(message) is False
