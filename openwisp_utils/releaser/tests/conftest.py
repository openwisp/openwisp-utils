import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def project_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def mock_config():
    return {"version_path": "path/__init__.py"}


def _create_setup_py(path: Path, name="my-test-package"):
    (path / "setup.py").write_text(
        f'from setuptools import setup\nsetup(name="{name}")'
    )


@pytest.fixture
def create_setup_py():
    return _create_setup_py


def _create_package_dir_with_version(
    path: Path, name="my-test-package", version_str="VERSION = (1, 2, 3, 'final')"
):
    pkg_dir = path / name.replace("-", "_")
    pkg_dir.mkdir(exist_ok=True)
    (pkg_dir / "__init__.py").write_text(version_str)


@pytest.fixture
def create_package_dir_with_version():
    return _create_package_dir_with_version


def _create_changelog(path: Path, ext="rst"):
    (path / f"CHANGES.{ext}").write_text("Changelog")


@pytest.fixture
def create_changelog():
    return _create_changelog


def _init_git_repo(
    path: Path, remote_url="https://github.com/my-org/my-test-package.git"
):
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=path, check=True)


@pytest.fixture
def init_git_repo():
    return _init_git_repo
