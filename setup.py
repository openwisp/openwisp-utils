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
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "checkmigrations = openwisp_utils.qa:check_migration_name",
            "checkcommit = openwisp_utils.qa:check_commit_message",
        ]
    },
    scripts=["openwisp-qa-check", "openwisp-qa-format", "openwisp-pre-push-hook"],
    zip_safe=False,
    install_requires=[
        "django-model-utils>=4.5,<5.1",
        "django-compress-staticfiles~=1.0.1b",
        "django-admin-autocomplete-filter~=0.7.1",
        "swapper~=1.4.0",
        # allow wider range here to avoid interfering with other modules
        "urllib3>=2.0.0,<3.0.0",
    ],
    extras_require={
        "qa": [
            "black~=24.10.0",
            "flake8~=7.2.0",
            "isort~=6.0.1",
            "coverage>=7.6.1,<7.9.0",
            "tblib~=3.1.0",
            "docstrfmt~=1.10.0",
        ],
        "rest": [
            "djangorestframework>=3.14,<3.15.2",
            "django-filter~=23.2",  # django-filter uses CalVer
            "drf-yasg~=1.21.7",
        ],
        "channels": [
            "channels[daphne]@"
            "git+https://github.com/openwisp/channels.git@"
            "issues/2148-ChannelsLiveServerTestCase-Django52-compatible#egg=channels[daphne]",
            "channels_redis~=4.2.1",
        ],
        "channels-test": [
            "pytest-asyncio>=0.24,<0.27",
            "pytest-django~=4.10.0",
        ],
        "celery": ["celery~=5.4.0"],
        "selenium": ["selenium>=4.10,<4.30"],
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
