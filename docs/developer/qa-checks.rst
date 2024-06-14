Quality Assurance Checks
------------------------

.. include:: ../partials/developer-docs.rst

This package contains some common QA checks that are used in the
automated builds of different OpenWISP modules.

``openwisp-qa-format``
^^^^^^^^^^^^^^^^^^^^^^

This shell script automatically formats Python and CSS code according
to the `OpenWISP coding style conventions <https://openwisp.io/docs/developer/contributing.html#coding-style-conventions>`_.

It runs ``isort`` and ``black`` to format python code
(these two dependencies are required and installed automatically when running
``pip install openwisp-utils[qa]``).

The ``stylelint`` and ``jshint`` programs are used to perform style checks on CSS and JS code respectively, but they are optional:
if ``stylelint`` and/or ``jshint`` are not installed, the check(s) will be skipped.

``openwisp-qa-check``
^^^^^^^^^^^^^^^^^^^^^

Shell script to run the following quality assurance checks:

* `checkmigrations <#checkmigrations>`_
* `checkcommit <#checkcommit>`_
* `checkendline <#checkendline>`_
* `checkpendingmigrations <#checkpendingmigrations>`_
* `checkrst <#checkrst>`_
* ``flake8`` - Python code linter
* ``isort`` - Sorts python imports alphabetically, and seperated into sections
* ``black`` - Formats python code using a common standard
* ``csslinter`` - Formats and checks CSS code using stylelint common standard
* ``jslinter`` - Checks Javascript code using jshint common standard

If a check requires a flag, it can be passed forward in the same way.

Usage example::

    openwisp-qa-check --migration-path <path> --message <commit-message>

Any unneeded checks can be skipped by passing ``--skip-<check-name>``

Usage example::

    openwisp-qa-check --skip-isort

For backward compatibility ``csslinter`` and ``jslinter`` are skipped by default.
To run them in checks pass arguements in this way.

Usage example::

    # To activate csslinter
    openwisp-qa-check --csslinter

    # To activate jslinter
    openwisp-qa-check --jslinter

You can do multiple ``checkmigrations`` by passing the arguments with space-delimited string.

For example, this multiple ``checkmigrations``::

    checkmigrations --migrations-to-ignore 3 \
            --migration-path ./openwisp_users/migrations/ || exit 1

    checkmigrations --migrations-to-ignore 2 \
            --migration-path ./tests/testapp/migrations/ || exit 1

Can be changed with::

    openwisp-qa-check --migrations-to-ignore "3 2" \
            --migration-path "./openwisp_users/migrations/ ./tests/testapp/migrations/"

``checkmigrations``
^^^^^^^^^^^^^^^^^^^

Ensures the latest migrations created have a human readable name.

We want to avoid having many migrations named like ``0003_auto_20150410_3242.py``.

This way we can reconstruct the evolution of our database schemas faster, with
less efforts and hence less costs.

Usage example::

    checkmigrations --migration-path ./django_freeradius/migrations/

``checkcommit``
^^^^^^^^^^^^^^^

Ensures the last commit message follows our `commit message style guidelines
<http://openwisp.io/docs/developer/contributing.html#commit-message-style-guidelines>`_.

We want to keep the commit log readable, consistent and easy to scan in order
to make it easy to analyze the history of our modules, which is also a very
important activity when performing maintenance.

Usage example::

    checkcommit --message "$(git log --format=%B -n 1)"

If, for some reason, you wish to skip this QA check for a specific commit message
you can add ``#noqa`` to the end of your commit message.

Usage example::

    [qa] Improved #20

    Simulation of a special unplanned case
    #noqa

``checkendline``
^^^^^^^^^^^^^^^^

Ensures that a blank line is kept at the end of each file.

``checkpendingmigrations``
^^^^^^^^^^^^^^^^^^^^^^^^^^

Ensures there django migrations are up to date and no new migrations need to
be created.

It accepts an optional ``--migration-module`` flag indicating the django app
name that should be passed to ``./manage.py makemigrations``, eg:
``./manage.py makemigrations $MIGRATION_MODULE``.

``checkrst``
^^^^^^^^^^^^^

Checks the syntax of all ReStructuredText files to ensure they can be published on pypi or using python-sphinx.
