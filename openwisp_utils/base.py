import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.fields import AutoCreatedField, AutoLastModifiedField

# For backward compatibility
from .fields import KeyField  # noqa


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedEditableModel(UUIDModel):
    """
    An abstract base class model that provides self-updating
    ``created`` and ``modified`` fields.
    """

    created = AutoCreatedField(_('created'), editable=True)
    modified = AutoLastModifiedField(_('modified'), editable=True)

    class Meta:
        abstract = True


class FallbackModelMixin(object):
    def get_field_value(self, field_name):
        value = getattr(self, field_name)
        field = self._meta.get_field(field_name)
        if value is None and hasattr(field, 'fallback'):
            return field.fallback
        return value
