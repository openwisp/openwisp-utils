import os
import subprocess
import tempfile
from pathlib import Path
from unittest import TestCase

import yaml


class TestWorkflowSecurity(TestCase):
    workflows = Path(__file__).resolve().parents[3] / ".github" / "workflows"

    def workflow(self, name):
        return yaml.safe_load((self.workflows / f"{name}.yml").read_text())

    def test_app_token_permissions(self):
        cases = {
            "reusable-version-branch": [{"contents": "write"}],
            "reusable-backport": [{"contents": "write", "pull-requests": "write"}],
            "reusable-bot-changelog": [{"pull-requests": "write", "issues": "read"}],
            "reusable-bot-ci-failure": [{"actions": "write", "pull-requests": "write"}],
            "reusable-bot-autoassign": [
                {"issues": "write", "pull-requests": "write"},
                {"issues": "read", "organization-projects": "read"},
            ],
        }
        for name, expected in cases.items():
            with self.subTest(workflow=name):
                tokens = []
                for job in self.workflow(name)["jobs"].values():
                    for step in job.get("steps", []):
                        if not step.get("uses", "").startswith(
                            "actions/create-github-app-token@"
                        ):
                            continue
                        self.assertEqual(job["environment"], "openwisp-bot")
                        inputs = step["with"]
                        self.assertEqual(
                            inputs["owner"], "${{ github.repository_owner }}"
                        )
                        grants = {
                            key.removeprefix("permission-"): value
                            for key, value in inputs.items()
                            if key.startswith("permission-")
                        }
                        tokens.append(grants)
                        if (
                            inputs["repositories"]
                            == "${{ env.PUBLIC_VALIDATION_REPOSITORIES }}"
                        ):
                            self.assertTrue(
                                all(value == "read" for value in grants.values())
                            )
                        else:
                            self.assertEqual(
                                inputs["repositories"],
                                "${{ github.event.repository.name }}",
                            )
                self.assertEqual(
                    tokens, expected, "App token grants must be explicit and minimal"
                )

    def test_app_secret_forwarding(self):
        for path in self.workflows.glob("*.yml"):
            workflow = self.workflow(path.stem)
            for name, job in workflow["jobs"].items():
                target = job.get("uses", "").split("/")[-1].split("@")[0]
                if not target.startswith("reusable-"):
                    continue
                with self.subTest(workflow=path.name, job=name):
                    self.assertEqual(
                        job["secrets"]["OPENWISP_BOT_PRIVATE_KEY"],
                        "${{ secrets.OPENWISP_BOT_PRIVATE_KEY }}",
                        "Environment-only App secrets must be explicitly forwarded by name",
                    )
                    called = self.workflow(target.removesuffix(".yml"))
                    trigger = called.get("on", called.get(True))
                    self.assertIn(
                        "OPENWISP_BOT_PRIVATE_KEY",
                        trigger["workflow_call"]["secrets"],
                    )

    def test_replication_trust_boundary(self):
        workflow = self.workflow("reusable-version-branch")
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        prepare, replicate = (
            workflow["jobs"][name] for name in ("prepare", "replicate")
        )
        for job in (prepare, replicate):
            with self.subTest(job=job):
                self.assertEqual(
                    job["if"],
                    "github.event_name == 'push' && github.ref == 'refs/heads/master'",
                )
                checkout = job["steps"][0]["with"]
                self.assertEqual(checkout["ref"], "${{ github.sha }}")
                self.assertIs(checkout["persist-credentials"], False)
        self.assertNotIn(
            "environment", prepare, "Package execution must not receive App secrets"
        )
        self.assertNotIn("secrets.", str(prepare))
        self.assertEqual(replicate["needs"], "prepare")
        self.assertEqual(replicate["environment"], "openwisp-bot")
        self.assertIs(replicate["concurrency"]["cancel-in-progress"], False)
        steps = replicate["steps"]
        self.assertEqual(steps[-2]["id"], "app-token")
        self.assertEqual(steps[-1]["name"], "Push version branch")
        self.assertNotIn("pip install", str(steps))
        self.assertNotIn("python", str(steps))
        self.assertEqual(
            steps[-1]["env"]["GH_TOKEN"], "${{ steps.app-token.outputs.token }}"
        )
        self.assertIn('push origin "HEAD:refs/heads/$VERSION"', steps[-1]["run"])
        self.assertNotIn("--force", steps[-1]["run"])
        caller = self.workflow("version-branch")
        self.assertEqual(caller["permissions"], {"contents": "read"})
        self.assertIn(
            "OPENWISP_BOT_APP_ID", caller["jobs"]["version-branch"]["secrets"]
        )

    def test_version_validation(self):
        steps = self.workflow("reusable-version-branch")["jobs"]["prepare"]["steps"]
        step = next(step for step in steps if step.get("id") == "get-version")
        self.assertNotIn(
            "${{", step["run"], "Inputs must not be interpolated into code"
        )
        cases = [
            ("package.module", "(1, 4, 'alpha', 0)", True),
            ("package.module", "(-1, 4)", False),
            ("package.module", "('1', 4)", False),
            ("package.module", "(True, 4)", False),
            ("package.module", "('1\\nother=value', 4)", False),
            ('package.module"; touch injected; #', "(1, 4)", False),
        ]
        for name, version, success in cases:
            with self.subTest(
                module=name, version=version
            ), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "package").mkdir()
                (root / "package" / "__init__.py").write_text("")
                (root / "package" / "module.py").write_text(f"VERSION = {version}\n")
                output = root / "output"
                result = subprocess.run(
                    ["bash", "-e", "-c", step["run"]],
                    cwd=root,
                    env={
                        **os.environ,
                        "MODULE_NAME": name,
                        "GITHUB_OUTPUT": str(output),
                    },
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode == 0, success, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertFalse((root / "injected").exists())
                if success:
                    self.assertEqual(output.read_text(), "version=1.4\n")
                else:
                    self.assertFalse(
                        output.exists(), "Invalid versions must not produce job outputs"
                    )

    def test_replication_rebase(self):
        steps = self.workflow("reusable-version-branch")["jobs"]["replicate"]["steps"]
        rebase = next(
            step["run"] for step in steps if step["name"].startswith("Rebase")
        )
        for existing in (False, True):
            with self.subTest(
                existing=existing
            ), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)

                def git(*args, cwd=root):
                    return subprocess.run(
                        ["git", *args],
                        cwd=cwd,
                        check=True,
                        capture_output=True,
                        text=True,
                    ).stdout.strip()

                git("init", "-b", "master")
                git("config", "user.name", "Test")
                git("config", "user.email", "test@example.org")
                (root / "file").write_text("initial")
                git("add", "file")
                git("commit", "-m", "Initial")
                if existing:
                    git("update-ref", "refs/remotes/origin/1.4", "HEAD")
                (root / "file").write_text("updated")
                git("commit", "-am", "Updated")
                sha = git("rev-parse", "HEAD")
                git("checkout", "--detach", sha)
                result = subprocess.run(
                    ["bash", "-e", "-c", rebase],
                    cwd=root,
                    env={**os.environ, "VERSION": "1.4", "GITHUB_SHA": sha},
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(git("rev-parse", "refs/heads/1.4"), sha)
