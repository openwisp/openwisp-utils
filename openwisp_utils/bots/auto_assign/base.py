import os

from github import Github


class GitHubBot:
    def __init__(self):
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.repository_name = os.environ.get("REPOSITORY")
        self.event_name = os.environ.get("GITHUB_EVENT_NAME")
        self.event_payload = None

        if self.github_token and self.repository_name:
            try:
                self.github = Github(self.github_token)
                self.repo = self.github.get_repo(self.repository_name)
            except Exception as e:
                print(f"Warning: Could not initialize GitHub client: {e}")
                self.github = None
                self.repo = None
        else:
            missing = []
            if not self.github_token:
                missing.append("GITHUB_TOKEN")
            if not self.repository_name:
                missing.append("REPOSITORY")
            print(f"Warning: Missing environment variables: {', '.join(missing)}")
            self.github = None
            self.repo = None

    def load_event_payload(self, event_payload):
        self.event_payload = event_payload
