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
    message = "[tests:fix] Good commit message"
    code, out, err = run_cz_check(message)
    assert code == 0


def test_valid_commit_without_body():
    message = "[qa] Good commit message #1\n\n" "Fixes #1"
    code, out, err = run_cz_check(message)
    assert code == 0


def test_merge_commits_ignored():
    message = "Merge branch 'master' into issues/110-commit-convention-standardization"
    code, out, err = run_cz_check(message)
    assert code == 0


def test_empty_commit_message():
    assert run_cz_check("") != 0


def test_invalid_prefix_format():
    message = "qa Good commit message #1\n\n" "Body\n\n" "Fixes #1"
    assert run_cz_check(message) != 0


def test_title_not_capitalized():
    message = "[qa] bad commit message #1\n\n" "Body\n\n" "Fixes #1"
    assert run_cz_check(message) != 0


def test_valid_commit_without_issue_number():
    message = "[qa] Good commit message\n\n" "Some explanation.\n\n" "Fixes #1"
    assert run_cz_check(message) != 0


def test_issue_number_not_at_end_of_title():
    message = "[qa] Good #1 commit message\n\n" "Body\n\n" "Fixes #1"
    assert run_cz_check(message) != 0


def test_missing_blank_line_after_header():
    message = "[qa] Good commit message #1\n" "Body\n\n" "Fixes #1"
    assert run_cz_check(message) != 0


def test_missing_blank_line_before_footer():
    message = "[qa] Good commit message #1\n\n" "Body\n" "Fixes #1"
    assert run_cz_check(message) != 0


def test_missing_fixes_footer():
    message = "[qa] Good commit message #1\n\n" "Body"
    assert run_cz_check(message) != 0


def test_footer_not_last_line():
    message = "[qa] Good commit message #1\n\n" "Body\n\n" "Fixes #1\n" "Extra line"
    assert run_cz_check(message) != 0


def test_mismatched_issue_numbers():
    message = "[qa] Good commit message #1\n\n" "Body\n\n" "Fixes #2"
    assert run_cz_check(message) != 0


def test_info_includes_all_prefixes():
    result = subprocess.run(
        ["cz", "info"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert result.returncode == 0
    # Check that all expected prefixes are listed
    assert "- feature" in result.stdout
    assert "- change" in result.stdout
    assert "- fix" in result.stdout
    assert "- docs" in result.stdout
    assert "- test" in result.stdout
    assert "- ci" in result.stdout
    assert "- chore" in result.stdout
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
    assert "Invalid commit message" in output
    assert "Expected format:" in output
    assert "[prefix]" in output
    assert "[feature]" in output
    assert "Fixes #<issue>" in output
    # Make sure raw regex pattern is NOT shown
    assert "(?sm)" not in output
    assert "pattern:" not in output.lower()
