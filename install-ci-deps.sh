#!/bin/bash
# Install QA tools and Python dependencies for the selected CI matrix row.
set -e

if [ "${CI_SYSTEM_DEPS_READY:-0}" != 1 ]; then
    sudo npm install -g prettier
fi
if [ "${CI_SYSTEM_DEPS_ONLY:-0}" = 1 ]; then
    exit 0
fi

python -m pip install -U pip wheel setuptools
python -m pip install -U -r requirements-test.txt
python -m pip install -e '.[qa,rest,selenium,celery,channels,releaser]'
python -m pip install "${DJANGO_VERSION:?Set DJANGO_VERSION to a CI matrix value}"
