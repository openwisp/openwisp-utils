Storage Utilities
-----------------

.. include:: ../partials/developer-docs.rst

.. _openwisp_utilsstorageCompressStaticFilesStorage:

``openwisp_utils.storage.CompressStaticFilesStorage``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A static storage backend for compression inheriting from `django-compress-staticfiles's <https://pypi.org/project/django-compress-staticfiles/>`_ ``CompressStaticFilesStorage`` class.

Adds support for excluding file types using :ref:`OPENWISP_STATICFILES_VERSIONED_EXCLUDE <openwisp_staticfiles_versioned_exclude>` setting.

To use point ``STATICFILES_STORAGE`` to ``openwisp_utils.storage.CompressStaticFilesStorage`` in ``settings.py``.

.. code-block:: python

    STATICFILES_STORAGE = 'openwisp_utils.storage.CompressStaticFilesStorage'
