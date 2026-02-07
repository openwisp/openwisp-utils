import subprocess


def run_cz_check(message):
    result = subprocess.run(
        ["cz", "check", "--message", message],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def test_valid_commit_message():
    message = "[qa] Good commit message #1\n\n" "Some explanation.\n\n" "Fixes #1"
    code, out, err = run_cz_check(message)
    assert code == 0


def test_valid_commit_message_simple():
    message = "[chores] Good commit message"
    code, out, err = run_cz_check(message)
    assert code == 0


def test_valid_commit_message_double_prefix():
    # Use [test:fix] instead of [tests:fix] since "test" is in ALLOWED_PREFIXES
    message = "[test:fix] Good commit message"
    code, out, err = run_cz_check(message)
    assert code == 0


def test_valid_commit_without_body():
    message = "[qa] Good commit message #1\n\n" "Fixes #1"
    code, out, err = run_cz_check(message)
    assert code == 0


def test_valid_commit_message_with_closes():
    # GitHub also accepts "Closes" keyword to close issues
    message = (
        "[feature:qa] Standardized commit messages #110\n\n"
        "Commitizen has been integrated.\n\n"
        "Closes #110"
    )
    code, out, err = run_cz_check(message)
    assert code == 0


def test_valid_commit_message_with_related_to():
    # "Related to" is used to reference issues without closing them
    message = (
        "[feature] Progress on feature #110\n\n"
        "Partial implementation.\n\n"
        "Related to #110"
    )
    code, out, err = run_cz_check(message)
    assert code == 0


def test_merge_commits_ignored():
    message = "Merge branch 'master' into issues/110-commit-convention-standardization"
    code, out, err = run_cz_check(message)
    assert code == 0


def test_empty_commit_message():
    code, out, err = run_cz_check("")
    assert code != 0


def test_invalid_prefix_format():
    message = "qa Good commit message #1\n\n" "Body\n\n" "Fixes #1"
    code, out, err = run_cz_check(message)
    assert code != 0


def test_title_not_capitalized():
    message = "[qa] bad commit message #1\n\n" "Body\n\n" "Fixes #1"
    code, out, err = run_cz_check(message)
    assert code != 0


def test_valid_commit_without_issue_number():
    message = "[qa] Good commit message\n\n" "Some explanation.\n\n" "Fixes #1"
    code, out, err = run_cz_check(message)
    assert code != 0


def test_issue_number_not_at_end_of_title():
    message = "[qa] Good #1 commit message\n\n" "Body\n\n" "Fixes #1"
    code, out, err = run_cz_check(message)
    assert code != 0


def test_missing_blank_line_after_header():
    message = "[qa] Good commit message #1\n" "Body\n\n" "Fixes #1"
    code, out, err = run_cz_check(message)
    assert code != 0


def test_missing_blank_line_before_footer():
    # Relaxed requirement: no blank line before footer is now allowed
    message = "[qa] Good commit message #1\n\n" "Body\n" "Fixes #1"
    code, out, err = run_cz_check(message)
    assert code == 0


def test_missing_fixes_footer():
    message = "[qa] Good commit message #1\n\n" "Body"
    code, out, err = run_cz_check(message)
    assert code != 0


def test_footer_not_last_line():
    message = "[qa] Good commit message #1\n\n" "Body\n\n" "Fixes #1\n" "Extra line"
    code, out, err = run_cz_check(message)
    assert code != 0


def test_mismatched_issue_numbers():
    message = "[qa] Good commit message #1\n\n" "Body\n\n" "Fixes #2"
    code, out, err = run_cz_check(message)
    assert code != 0


def test_info_includes_all_prefixes():
    result = subprocess.run(
        ["cz", "info"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert result.returncode == 0
    # Check that all expected prefixes are listed (exact match, not substring)
    assert "- feature" in result.stdout
    assert "- change" in result.stdout
    assert "- fix" in result.stdout
    assert "- docs" in result.stdout
    assert "- test" in result.stdout
    assert "- ci" in result.stdout
    assert "- chores" in result.stdout
    assert "- qa" in result.stdout
    assert "- deps" in result.stdout
    assert "- release" in result.stdout
    assert "- bump" in result.stdout


def test_error_message_is_user_friendly():
    message = "INVALID COMMIT MESSAGE"
    code, out, err = run_cz_check(message)
    assert code != 0
    output = out + err
    # Check that error message is user-friendly (not raw regex)
    assert "commit validation: failed!" in output
    assert "Invalid commit message format" in output
    assert "Expected format:" in output
    assert "[prefix]" in output
    assert "[feature]" in output
    assert "Fixes #<issue>" in output
    # Make sure raw regex pattern is NOT shown
    assert "(?sm)" not in output
    assert "pattern:" not in output.lower()
