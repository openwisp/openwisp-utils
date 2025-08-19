from unittest.mock import MagicMock, patch

import pytest
import requests
from openwisp_utils.releaser.github import GitHub
from openwisp_utils.releaser.utils import SkipSignal

MOCK_JSON_RESPONSE = {
    "html_url": "http://example.com",
    "merged": True,
    "default_branch": "main",
    "login": "testuser",
}


@pytest.fixture
def mock_response():
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = MOCK_JSON_RESPONSE
    response.status_code = 200  # Default success code
    return response


@pytest.fixture
def github_client():
    return GitHub(token="fake-token", repo="owner/repo")


def test_github_init_failures():
    with pytest.raises(ValueError, match="GitHub token is required"):
        GitHub(token=None, repo="owner/repo")
    with pytest.raises(ValueError, match="repository name .* is required"):
        GitHub(token="fake-token", repo=None)


@patch("openwisp_utils.releaser.github.retryable_request")
def test_create_pr(mock_retryable_request, github_client, mock_response):
    mock_retryable_request.return_value = mock_response
    url = github_client.create_pr("feature-branch", "main", "New Feature")
    assert url == "http://example.com"
    mock_retryable_request.assert_called_once()
    call_args = mock_retryable_request.call_args[1]
    assert call_args["url"].endswith("/pulls")
    assert call_args["json"]["title"] == "New Feature"


@patch("openwisp_utils.releaser.github.retryable_request")
def test_is_pr_merged(mock_retryable_request, github_client, mock_response):
    mock_retryable_request.return_value = mock_response
    merged = github_client.is_pr_merged("http://example.com/pull/123")
    assert merged is True
    call_args = mock_retryable_request.call_args[1]
    assert call_args["url"].endswith("/pulls/123")


@patch("openwisp_utils.releaser.github.retryable_request")
def test_create_release(mock_retryable_request, github_client, mock_response):
    mock_retryable_request.return_value = mock_response
    url = github_client.create_release("v1.0.0", "Version 1.0.0", "Release notes.")
    assert url == "http://example.com"
    call_args = mock_retryable_request.call_args[1]
    assert call_args["url"].endswith("/releases")
    assert call_args["json"]["tag_name"] == "v1.0.0"
    assert call_args["json"]["draft"] is True


@patch("requests.post")
@patch("openwisp_utils.releaser.github.retryable_request")
def test_check_pr_creation_permission(
    mock_retryable_request, mock_requests_post, github_client, mock_response
):
    mock_retryable_request.return_value = mock_response
    # Mock the final permission check call to return 422, which indicates success
    mock_requests_post.return_value = MagicMock(status_code=422)

    permission = github_client.check_pr_creation_permission()
    assert permission is True
    assert mock_retryable_request.call_count == 2  # repo and user calls
    mock_requests_post.assert_called_once()  # Final probe call


@patch("openwisp_utils.releaser.github.retryable_request", side_effect=SkipSignal)
def test_check_pr_creation_permission_skip(mock_retryable_request, github_client):
    permission = github_client.check_pr_creation_permission()
    assert permission is True  # Should gracefully continue, assuming permission


@patch("requests.post", side_effect=requests.RequestException("Network Error"))
@patch("openwisp_utils.releaser.github.retryable_request")
def test_check_pr_creation_permission_network_error(
    mock_retryable_request, mock_requests_post, github_client, mock_response
):
    mock_retryable_request.return_value = mock_response
    permission = github_client.check_pr_creation_permission()
    assert permission is False
