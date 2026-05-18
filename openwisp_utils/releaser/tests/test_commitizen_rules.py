import re
from types import SimpleNamespace

# ``commitizen.cz`` must be imported before ``openwisp_utils.releaser.commitizen``
# so its plugin auto-discovery completes first; otherwise discovery re-imports
# our module mid-initialization and raises AttributeError (issue #669).
import commitizen.cz  # noqa: F401, E402
from openwisp_utils.releaser.commitizen import OpenWispCommitizen  # noqa: E402

# Coverage was previously invisible because every test went through the
# ``cz`` subprocess; calling the plugin in-process keeps the existing
# assertions but lets the parent process's coverage tracker see the
# method bodies actually run.
_PLUGIN = OpenWispCommitizen(SimpleNamespace(settings={}))
_PATTERN = re.compile(_PLUGIN.schema_pattern())


def run_cz_check(message):
    """In-process equivalent of ``cz -n cz_openwisp check --message ...``.

    Returns ``(returncode, stdout, stderr)`` so the assertions written
    against the previous subprocess helper still apply.
    """
    result = _PLUGIN.validate_commit_message(
        commit_msg=message,
        pattern=_PATTERN,
        allow_abort=False,
        allowed_prefixes=[],
        max_msg_length=None,
        commit_hash="TEST",
    )
    if result.is_valid:
        return 0, "commit validation: successful!", ""
    return 1, "commit validation: failed!\n" + "\n".join(result.errors), ""


def test_valid_commit_with_issue():
    """Valid: issue in both title and body, matching."""
    message = "[qa] Good commit message #1\n\n" "Some explanation.\n\n" "Fixes #1"
    code, out, err = run_cz_check(message)
    assert code == 0, f"Expected success but got: {out + err}"


def test_valid_commit_without_issue():
    """Valid: no issue referenced at all."""
    message = "[chores] Good commit message\n\n" "Some explanation."
    code, out, err = run_cz_check(message)
    assert code == 0, f"Expected success but got: {out + err}"


def test_valid_commit_without_issue_single_line_body():
    """Valid: no issue, single line body without trailing punctuation."""
    message = "[chores] Good commit message\n\nSome explanation"
    code, out, err = run_cz_check(message)
    assert code == 0, f"Expected success but got: {out + err}"


def test_valid_commit_message_double_prefix():
    """Valid: double prefix like [tests:fix]."""
    message = "[tests:fix] Good commit message"
    code, out, err = run_cz_check(message)
    assert code == 0, f"Expected success but got: {out + err}"


def test_valid_commit_with_closes():
    """Valid: issue in both, using Closes keyword."""
    message = (
        "[feature:qa] Standardized commit messages #110\n\n"
        "Commitizen has been integrated.\n\n"
        "Closes #110"
    )
    code, out, err = run_cz_check(message)
    assert code == 0, f"Expected success but got: {out + err}"


def test_valid_commit_with_related_to():
    """Valid: issue in both, using Related to keyword."""
    message = (
        "[feature] Progress on feature #110\n\n"
        "Partial implementation.\n\n"
        "Related to #110"
    )
    code, out, err = run_cz_check(message)
    assert code == 0, f"Expected success but got: {out + err}"


def test_valid_commit_with_multiple_issues():
    """Valid: multiple issues in both title and body."""
    message = (
        "[feature] Fix bugs #123 #124\n\n"
        "Fixed multiple issues.\n\n"
        "Fixes #123\n"
        "Fixes #124"
    )
    code, out, err = run_cz_check(message)
    assert code == 0, f"Expected success but got: {out + err}"


def test_valid_commit_with_multiple_issues_same_line():
    """Valid: multiple issues on same line with single keyword."""
    message = (
        "[feature] Fix bugs #123 #124\n\n"
        "Fixed multiple issues.\n\n"
        "Fixes #123 #124"
    )
    code, out, err = run_cz_check(message)
    assert code == 0, f"Multiple issues on same line should work: {out + err}"


def test_merge_commits_ignored():
    """Valid: merge commits are always allowed."""
    message = "Merge branch 'master' into issues/110-commit-convention-standardization"
    code, out, err = run_cz_check(message)
    assert code == 0, f"Expected success but got: {out + err}"


def test_empty_commit_message():
    """Invalid: empty commit message."""
    code, out, err = run_cz_check("")
    assert code != 0


def test_invalid_prefix_format():
    """Invalid: missing square brackets around prefix."""
    message = "qa Good commit message #1\n\n" "Body\n\n" "Fixes #1"
    code, out, err = run_cz_check(message)
    assert code != 0


def test_title_not_capitalized():
    """Invalid: title doesn't start with capital letter."""
    message = "[qa] bad commit message #1\n\n" "Body\n\n" "Fixes #1"
    code, out, err = run_cz_check(message)
    assert code != 0


def test_issue_only_in_title():
    """Invalid: issue in title but not in body (asymmetric)."""
    message = "[qa] Good commit message #1\n\n" "Some explanation."
    code, out, err = run_cz_check(message)
    assert code != 0
    assert "title" in (out + err).lower()
    assert "body" in (out + err).lower()


def test_issue_only_in_body():
    """Invalid: issue in body but not in title (asymmetric)."""
    message = "[qa] Good commit message\n\n" "Some explanation.\n\n" "Fixes #1"
    code, out, err = run_cz_check(message)
    assert code != 0
    assert "body" in (out + err).lower()
    assert "title" in (out + err).lower()


def test_mismatched_issue_numbers():
    """Invalid: different issues in title and body."""
    message = "[qa] Good commit message #1\n\n" "Body\n\n" "Fixes #2"
    code, out, err = run_cz_check(message)
    assert code != 0
    assert "mismatch" in (out + err).lower() or "match" in (out + err).lower()


def test_issue_in_the_middle():
    """Valid: issue reference must be at end of title."""
    message = "[qa] Good #1 commit message\n\n" "Body\n\n" "Fixes #1"
    code, out, err = run_cz_check(message)
    assert code == 0, f"Issue in middle of title should still work: {out + err}"


def test_info_includes_all_prefixes():
    """Check that all expected prefixes are documented."""
    info = _PLUGIN.info()
    assert "- feature" in info
    assert "- change" in info
    assert "- fix" in info
    assert "- docs" in info
    assert "- tests" in info
    assert "- ci" in info
    assert "- chores" in info
    assert "- qa" in info
    assert "- deps" in info
    assert "- release" in info
    assert "- bump" in info


def test_error_message_is_user_friendly():
    """Check that error messages are helpful and don't expose regex."""
    message = "INVALID COMMIT MESSAGE"
    code, out, err = run_cz_check(message)
    assert code != 0
    output = out + err
    assert "commit validation: failed!" in output
    assert "Invalid commit message format" in output
    assert "Expected format:" in output
    assert "[prefix]" in output
    assert "[feature]" in output
    # Make sure raw regex pattern is NOT shown
    assert "(?sm)" not in output
    assert "pattern:" not in output.lower()


def test_error_message_for_asymmetric_issues():
    """Check that asymmetric issue errors are clear."""
    # Issue only in title
    message = "[qa] Good commit message #1\n\n" "Some explanation."
    code, out, err = run_cz_check(message)
    assert code != 0
    output = out + err
    assert "title" in output.lower()
    assert "body" in output.lower()
    assert "issue" in output.lower()


def test_valid_commit_with_auto_appended_related_to():
    """Valid: issue in title auto-appended to body as 'Related to'."""
    # This simulates what message() generates when title has issue but body doesn't
    message = (
        "[feature] Add new feature #123\n\n"
        "This adds a new feature.\n\n"
        "Related to #123"
    )
    code, out, err = run_cz_check(message)
    assert code == 0, f"Auto-appended Related to should be valid: {out + err}"


def test_valid_commit_with_multiple_auto_appended_issues():
    """Valid: multiple issues in title auto-appended to body."""
    message = (
        "[feature] Fix bugs #123 #124\n\n"
        "Fixed multiple issues.\n\n"
        "Related to #123\n"
        "Related to #124"
    )
    code, out, err = run_cz_check(message)
    assert code == 0, f"Multiple auto-appended issues should be valid: {out + err}"


def test_message_no_issue_returns_prefix_and_body():
    """message() builds a plain commit when neither title nor body reference an issue."""
    msg = _PLUGIN.message(
        {"change_type": "chores", "title": "Updated docs", "how": "Did stuff."}
    )
    assert msg == "[chores] Updated docs\n\nDid stuff."


def test_message_auto_appends_related_to_when_body_missing_issue():
    """message() auto-appends 'Related to' so the generated commit is symmetric."""
    msg = _PLUGIN.message(
        {
            "change_type": "feature",
            "title": "Added retries #42",
            "how": "Adds retry support.",
        }
    )
    assert msg.endswith("Related to #42")


def test_message_does_not_duplicate_issue_when_body_already_references_it():
    """If the user already referenced the issue in the body, nothing is appended."""
    msg = _PLUGIN.message(
        {
            "change_type": "feature",
            "title": "Added retries #42",
            "how": "Adds retry support.\n\nFixes #42",
        }
    )
    assert msg.count("#42") == 2  # one in title, one in body
    assert "Related to" not in msg


def test_questions_title_validator_rejects_lowercase():
    """The title prompt rejects titles that aren't capitalized."""
    title_validator = _PLUGIN.questions()[1]["validate"]
    assert title_validator("lowercase") == (
        "Commit title must start with a capital letter."
    )


def test_questions_title_validator_rejects_empty():
    """The title prompt rejects empty/whitespace-only input."""
    title_validator = _PLUGIN.questions()[1]["validate"]
    assert title_validator("   ") == "Commit title cannot be empty."


def test_questions_title_validator_accepts_capitalized():
    """The title prompt accepts titles that start with a capital letter."""
    title_validator = _PLUGIN.questions()[1]["validate"]
    assert title_validator("Capitalized title") is True


def test_subject_length_limit_exceeded():
    """validate_commit_message enforces max_msg_length on the subject line."""
    long_title = "[fix] X" + ("x" * 100)
    result = _PLUGIN.validate_commit_message(
        commit_msg=f"{long_title}\n\nBody.",
        pattern=_PATTERN,
        allow_abort=False,
        allowed_prefixes=[],
        max_msg_length=72,
        commit_hash="TEST",
    )
    assert result.is_valid is False
    assert "length" in result.errors[0].lower()


def test_format_error_message_returns_user_friendly_template():
    """format_error_message exposes the worked example, never the raw regex."""
    rendered = _PLUGIN.format_error_message("anything")
    assert rendered is OpenWispCommitizen.ERROR_TEMPLATE
    assert "(?sm)" not in rendered  # raw regex must not leak to users


def test_example_and_schema_match_documented_format():
    """example() and schema() are the strings the CLI surfaces to users."""
    assert _PLUGIN.example().startswith("[feature]")
    assert "Fixes #110" in _PLUGIN.example()
    assert _PLUGIN.schema() == "[<type>] <Title> [#<issue>]"
