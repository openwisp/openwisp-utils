Developer Installation Instructions
-----------------------------------

.. include:: ../partials/developer-docs.rst

Install Stable Version from Pypi
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install from pypi:

.. code-block:: shell

    pip install openwisp-utils

    # install optional dependencies for REST framework
    pip install openwisp-utils[rest]

    # install optional dependencies for tests (flake8, black and isort)
    pip install openwisp-utils[qa]

    # or install everything
    pip install openwisp-utils[rest,qa]

Install Development Version
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install tarball:

.. code-block:: shell

    pip install https://github.com/openwisp/openwisp-utils/tarball/master

Alternatively you can install via pip using git:

.. code-block:: shell

    pip install -e git+git://github.com/openwisp/openwisp-utils#egg=openwisp-utils

Installing for Development
~~~~~~~~~~~~~~~~~~~~~~~~~~

Install the system dependencies:

.. code-block:: shell

    sudo apt-get install sqlite3 libsqlite3-dev

    # For running E2E Selenium tests
    sudo apt install chromium

Install your forked repo:

.. code-block:: shell

    git clone git://github.com/<your_fork>/openwisp-utils
    cd openwisp-utils/
    pip install -e .[qa,rest]

Install test requirements:

.. code-block:: shell

    pip install -r requirements-test.txt

Install node dependencies used for testing:

.. code-block:: shell

    npm install -g stylelint jshint

Set up the pre-push hook to run tests and QA checks automatically right before the git push action, so that if anything fails the push operation will be aborted:

.. code-block:: shell

    openwisp-pre-push-hook --install

Install WebDriver for Chromium for your browser version from `<https://chromedriver.chromium.org/home>`_
and Extract ``chromedriver`` to one of directories from your ``$PATH`` (example: ``~/.local/bin/``).

Create database:

.. code-block:: shell

    cd tests/
    ./manage.py migrate
    ./manage.py createsuperuser

Run development server:

.. code-block:: shell

    cd tests/
    ./manage.py runserver

You can access the admin interface of the test project at http://127.0.0.1:8000/admin/.

Run tests with:

.. code-block:: shell

    ./runtests.py --parallel
