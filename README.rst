openwisp-utils
==============

.. image:: https://github.com/openwisp/openwisp-utils/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/openwisp/openwisp-utils/actions/workflows/ci.yml
    :alt: CI build status

.. image:: https://coveralls.io/repos/github/openwisp/openwisp-utils/badge.svg
    :target: https://coveralls.io/github/openwisp/openwisp-utils
    :alt: Test coverage

.. image:: https://img.shields.io/librariesio/release/github/openwisp/openwisp-utils
    :target: https://libraries.io/github/openwisp/openwisp-utils#repository_dependencies
    :alt: Dependency monitoring

.. image:: https://badge.fury.io/py/openwisp-utils.svg
    :target: http://badge.fury.io/py/openwisp-utils
    :alt: pypi

.. image:: https://pepy.tech/badge/openwisp-utils
    :target: https://pepy.tech/project/openwisp-utils
    :alt: downloads

.. image:: https://img.shields.io/gitter/room/nwjs/nw.js.svg?style=flat-square
    :target: https://gitter.im/openwisp/general
    :alt: support chat

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://pypi.org/project/black/
    :alt: code style: black

----

Python and Django functions, classes and settings re-used across different
OpenWISP modules, stored here with the aim of avoiding code duplication
and ease maintenance.

**Don't repeat yourself!**

.. image:: https://raw.githubusercontent.com/openwisp/openwisp2-docs/master/assets/design/openwisp-logo-black.svg
    :target: http://openwisp.org

Documentation
 WOFF files extracted
 using https://github.com/majodev/google-webfonts-helper.

Running tests locally (Windows PowerShell)
----------------------------------------

If you're on Windows, the included helper script will create a virtualenv, install deps and run tests.

From the repository root:

```powershell
.\run-tests.ps1
```

Alternatively, do the steps manually:

```powershell
# Create and activate venv
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
. .\.venv\Scripts\Activate.ps1

# Install package
pip install -e .[rest,qa]

# Install test requirements
pip install -r requirements-test.txt

# Run tests
python runtests.py
```

Notes:

- The `requirements-test.txt` installs `openwisp_controller` from the GitHub master tarball. This may take a while and can fail on very new Python versions.
- If you hit a `ModuleNotFoundError` (for example `openwisp_controller`), try installing the tarball manually:

```powershell
pip install "openwisp_controller @ https://github.com/openwisp/openwisp-controller/tarball/master"
```

If you want help running the tests or a CI setup, open an issue with the test failure output and your environment info.
  <https://openwisp.io/docs/stable/utils/developer/>`_

Contributing
------------

Please refer to the `OpenWISP contributing guidelines
<http://openwisp.io/docs/developer/contributing.html>`_.

Support
-------

See `OpenWISP Support Channels <http://openwisp.org/support.html>`_.

Changelog
---------

See `CHANGES
<https://github.com/openwisp/openwisp-utils/blob/master/CHANGES.rst>`_.

License
-------

See `LICENSE
<https://github.com/openwisp/openwisp-utils/blob/master/LICENSE>`_.

Attribution
-----------

- `Wireless icon
  <https://github.com/openwisp/openwisp-utils/blob/master/openwisp_utils/admin_theme/static/ui/openwisp/images/monitoring-wifi.svg>`_
  is licensed by Gregbaker, under `CC BY-SA 4.0
  <https://creativecommons.org/licenses/by-sa/4.0>`_ , via `Wikimedia
  Commons <https://commons.wikimedia.org/wiki/File:Wireless-icon.svg>`_.
- `Roboto webfont <https://www.google.com/fonts/specimen/Roboto>`_ is
  licensed under the `Apache License, Version 2.0
  <https://www.apache.org/licenses/LICENSE-2.0>`_. WOFF files extracted
  using https://github.com/majodev/google-webfonts-helper.
