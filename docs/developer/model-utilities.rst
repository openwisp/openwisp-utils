Model Utilities
---------------

.. include:: ../partials/developer-docs.rst

``openwisp_utils.base.UUIDModel``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Model class which provides a UUID4 primary key.

``openwisp_utils.base.TimeStampedEditableModel``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Model class inheriting ``UUIDModel`` which provides two additional fields:

- ``created``
- ``modified``

Which use respectively ``AutoCreatedField``, ``AutoLastModifiedField`` from ``model_utils.fields``
(self-updating fields providing the creation date-time and the last modified date-time).

``openwisp_utils.base.FallBackModelMixin``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Model mixin that implements ``get_field_value`` method which can be used
to get value of fallback fields.
