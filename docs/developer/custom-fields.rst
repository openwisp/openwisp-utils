Custom Fields
=============

.. include:: ../partials/developer-docs.rst

This section describes custom fields defined in ``openwisp_utils.fields``
that can be used in Django models.

.. contents:: **Table of Contents**:
    :depth: 2
    :local:

``openwisp_utils.fields.KeyField``
----------------------------------

A model field which provides a random key or token, widely used across
openwisp modules.

``openwisp_utils.fields.FallbackBooleanChoiceField``
----------------------------------------------------

This field extends Django's `BooleanField
<https://docs.djangoproject.com/en/4.2/ref/models/fields/#booleanfield>`_
and provides additional functionality for handling choices with a fallback
value.

.. include:: ../partials/fallback-fields.rst

This field is particularly useful when you want to present a choice
between enabled and disabled options.

.. code-block:: python

    from django.db import models
    from openwisp_utils.fields import FallbackBooleanChoiceField
    from myapp import settings as app_settings


    class MyModel(models.Model):
        is_active = FallbackBooleanChoiceField(
            fallback=app_settings.IS_ACTIVE_FALLBACK,
        )

``openwisp_utils.fields.FallbackCharChoiceField``
-------------------------------------------------

This field extends Django's `CharField
<https://docs.djangoproject.com/en/4.2/ref/models/fields/#charfield>`_ and
provides additional functionality for handling choices with a fallback
value.

.. include:: ../partials/fallback-fields.rst

.. code-block:: python

    from django.db import models
    from openwisp_utils.fields import FallbackCharChoiceField
    from myapp import settings as app_settings


    class MyModel(models.Model):
        is_first_name_required = FallbackCharChoiceField(
            max_length=32,
            choices=(
                ("disabled", _("Disabled")),
                ("allowed", _("Allowed")),
                ("mandatory", _("Mandatory")),
            ),
            fallback=app_settings.IS_FIRST_NAME_REQUIRED,
        )

``openwisp_utils.fields.FallbackCharField``
-------------------------------------------

This field extends Django's `CharField
<https://docs.djangoproject.com/en/4.2/ref/models/fields/#charfield>`_ and
provides additional functionality for handling text fields with a fallback
value.

.. include:: ../partials/fallback-fields.rst

.. code-block:: python

    from django.db import models
    from openwisp_utils.fields import FallbackCharField
    from myapp import settings as app_settings


    class MyModel(models.Model):
        greeting_text = FallbackCharField(
            max_length=200,
            fallback=app_settings.GREETING_TEXT,
        )

``openwisp_utils.fields.FallbackURLField``
------------------------------------------

This field extends Django's `URLField
<https://docs.djangoproject.com/en/4.2/ref/models/fields/#urlfield>`_ and
provides additional functionality for handling URL fields with a fallback
value.

.. include:: ../partials/fallback-fields.rst

.. code-block:: python

    from django.db import models
    from openwisp_utils.fields import FallbackURLField
    from myapp import settings as app_settings


    class MyModel(models.Model):
        password_reset_url = FallbackURLField(
            max_length=200,
            fallback=app_settings.DEFAULT_PASSWORD_RESET_URL,
        )

``openwisp_utils.fields.FallbackTextField``
-------------------------------------------

This extends Django's `TextField
<https://docs.djangoproject.com/en/4.2/ref/models/fields/#django.db.models.TextField>`_
and provides additional functionality for handling text fields with a
fallback value.

.. include:: ../partials/fallback-fields.rst

.. code-block:: python

    from django.db import models
    from openwisp_utils.fields import FallbackTextField
    from myapp import settings as app_settings


    class MyModel(models.Model):
        extra_config = FallbackTextField(
            max_length=200,
            fallback=app_settings.EXTRA_CONFIG,
        )

``openwisp_utils.fields.FallbackPositiveIntegerField``
------------------------------------------------------

This extends Django's `PositiveIntegerField
<https://docs.djangoproject.com/en/4.2/ref/models/fields/#positiveintegerfield>`_
and provides additional functionality for handling positive integer fields
with a fallback value.

.. include:: ../partials/fallback-fields.rst

.. code-block:: python

    from django.db import models
    from openwisp_utils.fields import FallbackPositiveIntegerField
    from myapp import settings as app_settings


    class MyModel(models.Model):
        count = FallbackPositiveIntegerField(
            fallback=app_settings.DEFAULT_COUNT,
        )

``openwisp_utils.fields.FallbackDecimalField``
----------------------------------------------

This extends Django's `DecimalField
<https://docs.djangoproject.com/en/4.2/ref/models/fields/#decimalfield>`_
and provides additional functionality for handling decimal fields with a
fallback value.

.. include:: ../partials/fallback-fields.rst

.. code-block:: python

    from django.db import models
    from openwisp_utils.fields import FallbackDecimalField
    from myapp import settings as app_settings


    class MyModel(models.Model):
        price = FallbackDecimalField(
            max_digits=4,
            decimal_places=2,
            fallback=app_settings.DEFAULT_PRICE,
        )
