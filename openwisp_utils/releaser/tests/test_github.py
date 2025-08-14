from unittest.mock import MagicMock, patch

import pytest
from openwisp_utils.releaser.github import GitHub

MOCK_RESPONSE = MagicMock()
MOCK_RESPONSE.raise_for_status.return_value = None
MOCK_RESPONSE.json.return_value = {
    "html_url": "http://example.com",
    "merged": True,
    "default_branch": "main",
    "login": "testuser",
}
MOCK_RESPONSE.status_code = 422


@pytest.fixture
def github_client():
    return GitHub(token="fake-token", repo="owner/repo")


def test_github_init_failures():
    with pytest.raises(ValueError, match="GitHub token is required"):
        GitHub(token=None, repo="owner/repo")
    with pytest.raises(ValueError, match="repository name .* is required"):
        GitHub(token="fake-token", repo=None)


@patch("openwisp_utils.releaser.github.retryable_request", return_value=MOCK_RESPONSE)
def test_create_pr(mock_request, github_client):
    url = github_client.create_pr("feature-branch", "main", "New Feature")
    assert url == "http://example.com"
    mock_request.assert_called_once()
    call_args = mock_request.call_args[1]
    assert call_args["url"].endswith("/pulls")
    assert call_args["json"]["title"] == "New Feature"


@patch("openwisp_utils.releaser.github.retryable_request", return_value=MOCK_RESPONSE)
def test_is_pr_merged(mock_request, github_client):
    merged = github_client.is_pr_merged("http://example.com/pull/123")
    assert merged is True
    call_args = mock_request.call_args[1]
    assert call_args["url"].endswith("/pulls/123")


@patch("openwisp_utils.releaser.github.retryable_request", return_value=MOCK_RESPONSE)
def test_create_release(mock_request, github_client):
    url = github_client.create_release("v1.0.0", "Version 1.0.0", "Release notes.")
    assert url == "http://example.com"
    call_args = mock_request.call_args[1]
    assert call_args["url"].endswith("/releases")
    assert call_args["json"]["tag_name"] == "v1.0.0"
    assert call_args["json"]["draft"] is True


@patch("openwisp_utils.releaser.github.retryable_request", return_value=MOCK_RESPONSE)
def test_check_pr_creation_permission(mock_request, github_client):
    permission = github_client.check_pr_creation_permission()
    assert permission is True
    assert mock_request.call_count == 3  # repo, user, and pulls calls
