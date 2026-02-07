#!/usr/bin/env python
from openwisp_utils import get_version
from setuptools import find_packages, setup

setup(
    name="openwisp-utils",
    version=get_version(),
    license="BSD-3-Clause",
    author="Various",
    author_email="support@openwisp.io",
    description="OpenWISP 2 Utilities",
    long_description=open("README.rst").read(),
    url="http://openwisp.org",
    download_url="https://github.com/openwisp/openwisp-utils/releases",
    platforms=["Platform Independent"],
    keywords=["django", "netjson", "openwrt", "networking", "openwisp"],
    packages=find_packages(exclude=["tests*", "docs*"]),
    entry_points={
        "console_scripts": [
            "checkmigrations = openwisp_utils.qa:check_migration_name",
            "checkcommit = openwisp_utils.qa:check_commit_message",
        ],
        # We override the default 'cz_conventional_commits' plugin to enforce the OpenWISP
        # commit message standard across all OpenWISP repositories without requiring
        # additional configuration in each repo. This ensures consistency and reduces
        # maintenance overhead.
        "commitizen.plugin": [
            "cz_conventional_commits = openwisp_utils.releaser.commitizen:OpenWispCommitizen",
        ],
    },
    include_package_data=True,
    scripts=["openwisp-qa-check", "openwisp-qa-format", "openwisp-pre-push-hook"],
    zip_safe=False,
    install_requires=[
        "django-model-utils>=4.5,<5.1",
        "django-minify-compress-staticfiles~=1.1.0",
        "django-admin-autocomplete-filter~=0.7.1",
        "swapper~=1.4.0",
        # allow wider range here to avoid interfering with other modules
        "urllib3>=2.0.0,<3.0.0",
        "distro~=1.9.0",
    ],
    extras_require={
        "qa": [
            "black>=25.1,<25.13",
            "flake8~=7.3.0",
            "isort>=6.0.1,<7.1.0",
            "coverage>=7.10.0,<7.14.0",
            "tblib~=3.2.2",
            "docstrfmt>=2.0.0,<2.1.0",
            "commitizen>=4.13.0,<5.0.0",
        ],
        "rest": [
            "djangorestframework~=3.16.0",
            "django-filter>=25.1,<26.0",  # django-filter uses CalVer
            "drf-yasg>=1.21.14,<1.22.0",
        ],
        "channels": [
            "channels[daphne]~=4.3.0",
            "channels_redis>=4.2.1,<4.4.0",
        ],
        "channels-test": [
            "pytest-asyncio>=1.3.0,<1.4.0",
            "pytest-django>=4.10,<4.12",
        ],
        "celery": ["celery~=5.6.1"],
        "selenium": ["selenium>=4.10,<4.41"],
        "releaser": [
            "git-cliff~=2.12.0",
            "questionary~=2.1.0",
            "pypandoc~=1.15",
            "pypandoc-binary~=1.15",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: System :: Networking",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Framework :: Django",
        "Programming Language :: Python :: 3",
    ],
)
