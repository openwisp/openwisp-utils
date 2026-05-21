from copy import copy

from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models
from django.db.models.fields.reverse_related import ForeignObjectRel

try:
    from rest_framework import serializers
    from rest_framework.exceptions import ValidationError as DRFValidationError
except ImportError:  # pragma: nocover
    raise ImproperlyConfigured(
        "Django REST Framework is required to use "
        "this feature but it is not installed"
    )


class ValidatedModelSerializer(serializers.ModelSerializer):
    exclude_validation = None

    def validate(self, data):
        """Performs model validation on serialized data.

        Allows to avoid having to duplicate model validation logic in the
        REST API.
        """
        instance = self.instance
        if not instance:
            Model = self.Meta.model
            instance = Model()
        else:
            instance = copy(instance)
        for key, value in data.items():
            Model = type(instance)
            # avoid direct assignment for m2m (not allowed)
            try:
                field = Model._meta.get_field(key)
            except Exception:
                continue
            if isinstance(field, (models.ManyToManyField, ForeignObjectRel)):
                continue
            setattr(instance, key, value)
        try:
            instance.full_clean(exclude=self.exclude_validation)
        except DjangoValidationError as e:
            raise DRFValidationError(detail=serializers.as_serializer_error(e))
        return data
