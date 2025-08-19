from unittest.mock import ANY, MagicMock, patch

import requests
from openwisp_utils.releaser.release import get_ai_summary

SAMPLE_CONTENT = "## [Unreleased]\n\n- feat: A new feature\n- fix: A bug fix"
AI_SUMMARY = "### Features\n\n- Added a cool new feature.\n\n### Bug Fixes\n\n- Fixed a critical bug."


@patch("openwisp_utils.releaser.release.questionary")
def test_get_ai_summary_user_declines(mock_questionary):
    """Tests that if the user declines the AI summary, the original content is returned."""
    mock_questionary.confirm.return_value.ask.return_value = False
    result = get_ai_summary(SAMPLE_CONTENT, "rst", "fake-token")
    assert result == SAMPLE_CONTENT
    mock_questionary.confirm.assert_called_once()


@patch("openwisp_utils.releaser.release.questionary")
@patch("builtins.print")
def test_get_ai_summary_no_token(mock_print, mock_questionary):
    """Tests that if the AI is requested but the token is missing, it skips and returns original content."""
    mock_questionary.confirm.return_value.ask.return_value = True
    result = get_ai_summary(SAMPLE_CONTENT, "rst", token=None)
    assert result == SAMPLE_CONTENT
    mock_print.assert_called_with(
        "⚠️ OPENAI_CHATGPT_TOKEN environment variable is not set. Skipping AI summary.",
        file=ANY,
    )


@patch("requests.post")
@patch("openwisp_utils.releaser.release.questionary")
def test_get_ai_summary_success_accepted(mock_questionary, mock_requests_post):
    """Tests the successful flow where the AI generates a summary and the user accepts it."""
    # User agrees to use AI and accepts the result
    mock_questionary.confirm.return_value.ask.return_value = True
    mock_questionary.select.return_value.ask.return_value = "Accept"

    # Mock the API response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": AI_SUMMARY}}]
    }
    mock_response.raise_for_status.return_value = None
    mock_requests_post.return_value = mock_response

    result = get_ai_summary(SAMPLE_CONTENT, "rst", "fake-token")

    assert result == AI_SUMMARY
    mock_requests_post.assert_called_once()


@patch("requests.post")
@patch("openwisp_utils.releaser.release.questionary")
def test_get_ai_summary_retry_and_accept(mock_questionary, mock_requests_post):
    """Tests the flow where the user retries AI generation and then accepts."""
    mock_questionary.confirm.return_value.ask.return_value = True
    mock_questionary.select.return_value.ask.side_effect = ["Retry", "Accept"]

    # Mock the API response for two calls
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": AI_SUMMARY}}]
    }
    mock_response.raise_for_status.return_value = None
    mock_requests_post.return_value = mock_response

    result = get_ai_summary(SAMPLE_CONTENT, "rst", "fake-token")

    assert result == AI_SUMMARY
    assert mock_requests_post.call_count == 2


@patch("requests.post", side_effect=requests.RequestException("API down"))
@patch("openwisp_utils.releaser.release.questionary")
def test_get_ai_summary_api_error(mock_questionary, mock_requests_post):
    """Tests that if the API call fails, the original content is returned."""
    mock_questionary.confirm.return_value.ask.return_value = True

    result = get_ai_summary(SAMPLE_CONTENT, "rst", "fake-token")

    assert result == SAMPLE_CONTENT


@patch("openwisp_utils.releaser.release.questionary")
@patch("requests.post")
def test_get_ai_summary_user_selects_original(mock_requests, mock_questionary):
    """Tests the flow where the user requests an AI summary but then chooses to use the original."""
    mock_questionary.confirm.return_value.ask.return_value = True
    mock_questionary.select.return_value.ask.return_value = (
        "Use Original (from git-cliff)"
    )
    original_content = "Original changelog"
    result = get_ai_summary(original_content, "rst", "fake-token")
    assert result == original_content
    mock_requests.assert_called_once()


@patch("openwisp_utils.releaser.release.questionary")
@patch("requests.post")
def test_get_ai_summary_invalid_decision_fallback(mock_requests, mock_questionary):
    """Tests the `else` fallback if the user's decision is not recognized."""
    mock_questionary.confirm.return_value.ask.return_value = True
    mock_questionary.select.return_value.ask.return_value = "Invalid Option"
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "AI Summary"}}]
    }
    mock_requests.return_value = mock_response
    original_content = "Original changelog"
    result = get_ai_summary(original_content, "rst", "fake-token")
    assert result == original_content
