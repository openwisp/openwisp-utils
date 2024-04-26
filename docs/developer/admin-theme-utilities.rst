Admin Theme utilities
---------------------

.. include:: /partials/developers-docs-warning.rst

``openwisp_utils.admin_theme.email.send_email``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This function allows sending email in both plain text and HTML version (using the template
and logo that can be customised using `OPENWISP_EMAIL_TEMPLATE <#openwisp_email_template>`_
and `OPENWISP_EMAIL_LOGO <#openwisp_email_logo>`_ respectively).

In case the HTML version if not needed it may be disabled by
setting `OPENWISP_HTML_EMAIL <#openwisp_html_email>`_ to ``False``.

**Syntax:**

.. code-block:: python

    send_email(subject, body_text, body_html, recipients, **kwargs)

+--------------------+--------------------------------------------------------------------------------------------+
| **Parameter**      | **Description**                                                                            |
+--------------------+--------------------------------------------------------------------------------------------+
| ``subject``        | (``str``) The subject of the email template.                                               |
+--------------------+--------------------------------------------------------------------------------------------+
| ``body_text``      | (``str``) The body of the text message to be emailed.                                      |
+--------------------+--------------------------------------------------------------------------------------------+
| ``body_html``      | (``str``) The body of the html template to be emailed.                                     |
+--------------------+--------------------------------------------------------------------------------------------+
| ``recipients``     | (``list``) The list of recipients to send the mail to.                                     |
+--------------------+--------------------------------------------------------------------------------------------+
| ``extra_context``  | **optional** (``dict``) Extra context which is passed to the template.                     |
|                    | The dictionary keys ``call_to_action_text`` and ``call_to_action_url``                     |
|                    | can be passed to show a call to action button.                                             |
|                    | Similarly, ``footer`` can be passed to add a footer.                                       |
+--------------------+--------------------------------------------------------------------------------------------+
| ``**kwargs``       | Any additional keyword arguments (e.g. ``attachments``, ``headers``, etc.)                 |
|                    | are passed directly to the `django.core.mail.EmailMultiAlternatives                        |
|                    | <https://docs.djangoproject.com/en/4.1/topics/email/#sending-alternative-content-types>`_. |
+--------------------+--------------------------------------------------------------------------------------------+


**Note**: Data passed in body should be validated and user supplied data should not be sent directly to the function.
