Using the ``admin_theme``
=========================

.. include:: ../partials/developer-docs.rst

.. contents:: **Table of Contents**:
    :depth: 2
    :local:

**The admin theme requires Django >= 2.2.**.

Make sure ``openwisp_utils.admin_theme`` is listed in ``INSTALLED_APPS``
(``settings.py``):

.. code-block:: python

    INSTALLED_APPS = [
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "openwisp_utils.admin_theme",  # <----- add this
        # add when using autocomplete filter
        "admin_auto_filters",  # <----- add this
        "django.contrib.sites",
        # admin
        "django.contrib.admin",
    ]

Using ``DependencyLoader`` and ``DependencyFinder``
---------------------------------------------------

Add the list of all packages extended to ``EXTENDED_APPS`` in
``settings.py``.

For example, if you've extended ``django_x509``:

.. code-block:: python

    EXTENDED_APPS = ["django_x509"]

``DependencyFinder``
~~~~~~~~~~~~~~~~~~~~

This is a static finder which looks for static files in the ``static``
directory of the apps listed in ``settings.EXTENDED_APPS``.

Add ``openwisp_utils.staticfiles.DependencyFinder`` to
``STATICFILES_FINDERS`` in ``settings.py``.

.. code-block:: python

    STATICFILES_FINDERS = [
        "django.contrib.staticfiles.finders.FileSystemFinder",
        "django.contrib.staticfiles.finders.AppDirectoriesFinder",
        "openwisp_utils.staticfiles.DependencyFinder",  # <----- add this
    ]

``DependencyLoader``
~~~~~~~~~~~~~~~~~~~~

This is a template loader which looks for templates in the ``templates``
directory of the apps listed in ``settings.EXTENDED_APPS``.

Add ``openwisp_utils.loaders.DependencyLoader`` to template ``loaders`` in
``settings.py`` as shown below.

.. code-block:: python

    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "OPTIONS": {
                "loaders": [
                    # ... other loaders ...
                    "openwisp_utils.loaders.DependencyLoader",  # <----- add this
                ],
                "context_processors": [
                    # ... omitted ...
                ],
            },
        },
    ]

.. _utils_custom_admin_theme:

Supplying Custom CSS and JS for the Admin Theme
-----------------------------------------------

Add ``openwisp_utils.admin_theme.context_processor.admin_theme_settings``
to template ``context_processors`` in ``settings.py`` as shown below. This
will allow to set :ref:`OPENWISP_ADMIN_THEME_LINKS
<openwisp_admin_theme_links>` and :ref:`OPENWISP_ADMIN_THEME_JS
<openwisp_admin_theme_js>` settings to provide CSS and JS files to
customize admin theme.

.. code-block:: python

    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "OPTIONS": {
                "loaders": [
                    # ... omitted ...
                ],
                "context_processors": [
                    # ... other context processors ...
                    "openwisp_utils.admin_theme.context_processor.admin_theme_settings"  # <----- add this
                ],
            },
        },
    ]

.. note::

    You will have to deploy these static files on your own.

    In order to make django able to find and load these files you may want
    to use the ``STATICFILES_DIR`` setting in ``settings.py``.

    You can learn more in the `Django documentation
    <https://docs.djangoproject.com/en/4.2/ref/settings/#std:setting-STATICFILES_DIRS>`_.

Extend Admin Theme Programmatically
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``openwisp_utils.admin_theme.theme.register_theme_link``
++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Allows adding items to :ref:`OPENWISP_ADMIN_THEME_LINKS
<openwisp_admin_theme_links>`.

This function is meant to be used by third party apps or OpenWISP modules
which aim to extend the core look and feel of the OpenWISP theme (e.g.:
add new menu icons).

**Syntax:**

.. code-block:: python

    register_theme_link(links)

============= ==============================================
**Parameter** **Description**
``links``     (``list``) List of *link* items to be added to
              :ref:`OPENWISP_ADMIN_THEME_LINKS
              <openwisp_admin_theme_links>`
============= ==============================================

``openwisp_utils.admin_theme.theme.unregister_theme_link``
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Allows removing items from :ref:`OPENWISP_ADMIN_THEME_LINKS
<openwisp_admin_theme_links>`.

This function is meant to be used by third party apps or OpenWISP modules
which aim additional functionalities to UI of OpenWISP (e.g.: adding a
support chat bot).

**Syntax:**

.. code-block:: python

    unregister_theme_link(links)

============= ==================================================
**Parameter** **Description**
``links``     (``list``) List of *link* items to be removed from
              :ref:`OPENWISP_ADMIN_THEME_LINKS
              <openwisp_admin_theme_links>`
============= ==================================================

``openwisp_utils.admin_theme.theme.register_theme_js``
++++++++++++++++++++++++++++++++++++++++++++++++++++++

Allows adding items to :ref:`OPENWISP_ADMIN_THEME_JS
<openwisp_admin_theme_JS>`.

**Syntax:**

.. code-block:: python

    register_theme_js(js)

============= ===========================================================
**Parameter** **Description**
``js``        (``list``) List of relative path of *js* files to be added
              to :ref:`OPENWISP_ADMIN_THEME_JS <openwisp_admin_theme_js>`
============= ===========================================================

``openwisp_utils.admin_theme.theme.unregister_theme_js``
++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Allows removing items from :ref:`OPENWISP_ADMIN_THEME_JS
<openwisp_admin_theme_JS>`.

**Syntax:**

.. code-block:: python

    unregister_theme_js(js)

============= ============================================================
**Parameter** **Description**
``js``        (``list``) List of relative path of *js* files to be removed
              from :ref:`OPENWISP_ADMIN_THEME_JS
              <openwisp_admin_theme_js>`
============= ============================================================

Sending emails
~~~~~~~~~~~~~~

.. _utils_send_email:

``openwisp_utils.admin_theme.email.send_email``
+++++++++++++++++++++++++++++++++++++++++++++++

This function enables sending emails in both plain text and HTML formats.
The HTML version uses a customizable template and logo.

You can set the logo using the :ref:`OPENWISP_EMAIL_LOGO
<openwisp_email_logo>` setting. To override the default template, see
:ref:`Customizing Email Templates <utils_send_email>`.

In case the HTML version if not needed it may be disabled by setting
:ref:`OPENWISP_HTML_EMAIL <openwisp_html_email>` to ``False``.

**Syntax:**

.. code-block:: python

    send_email(subject, body_text, body_html, recipients, **kwargs)

====================== ==========================================================================================
**Parameter**          **Description**
``subject``            (``str``) The subject of the email template.
``body_text``          (``str``) The body of the text message to be emailed.
``body_html``          (``str``) The body of the html template to be emailed.
``recipients``         (``list``) The list of recipients to send the mail to.
``extra_context``      **optional** (``dict``) Extra context which is passed to the template. The dictionary keys
                       ``call_to_action_text`` and ``call_to_action_url`` can be passed to show a call to action
                       button. Similarly, ``footer`` can be passed to add a footer.
``html_body_template`` **(optional, str)** The path to the template used for generating the HTML version. By
                       default, it uses ``openwisp_utils/email_template.html``.
``**kwargs``           Any additional keyword arguments (e.g. ``attachments``, ``headers``, etc.) are passed
                       directly to the `django.core.mail.EmailMultiAlternatives
                       <https://docs.djangoproject.com/en/4.1/topics/email/#sending-alternative-content-types>`_.
====================== ==========================================================================================

.. important::

    Data passed in body should be validated and user supplied data should
    not be sent directly to the function.

Customizing Email Templates
+++++++++++++++++++++++++++

To customize the email templates used by the :ref:`utils_send_email`
function, you can override the ``openwisp_utils/email_template.html``
template in your Django project. Create a template with the same path
(``openwisp_utils/email_template.html``) in your project's template
directory to override the default template.

It is recommended to extend the default email template as shown below:

.. code-block:: django

    {% extends 'openwisp_utils/email_template.html' %}
    {% block styles %}
    {{ block.super }}
    <style>
      .body {
        height: 100%;
        background: linear-gradient(to bottom, #8ccbbe 50%, #3797a4 50%);
        background-repeat: no-repeat;
        background-attachment: fixed;
        padding: 50px;
      }
    </style>
    {% endblock styles %}

Similarly, you can customize the HTML of the template by overriding the
``body`` block. See `email_template.html
<https://github.com/openwisp/openwisp-utils/blob/master/openwisp_utils/admin_theme/templates/openwisp_utils/email_template.html>`_
for reference implementation.
