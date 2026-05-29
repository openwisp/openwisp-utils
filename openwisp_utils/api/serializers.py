from copy import copy

from django.core.exceptions import ImproperlyConfigured

try:
    from django.core.exceptions import FieldDoesNotExist
    from django.core.exceptions import ValidationError as DjangoValidationError
    from django.db import models
    from django.db.models.fields.reverse_related import ForeignObjectRel
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
        Model = self.Meta.model
        # if instance is empty (eg: creation)
        # simulate for validation purposes
        if not instance:
            instance = Model()
        else:
            # Validate incoming PUT/PATCH data without mutating the DB instance.
            instance = copy(instance)
        for key, value in data.items():
            # avoid direct assignment for m2m (not allowed)
            try:
                field = Model._meta.get_field(key)
            except FieldDoesNotExist:
                continue
            if isinstance(field, (models.ManyToManyField, ForeignObjectRel)):
                continue
            # Skip nested relationships as we are only validating this model instance.
            if field.is_relation and isinstance(value, (dict, list)):
                continue
            setattr(instance, key, value)
        # perform model validation
        try:
            instance.full_clean(exclude=self.exclude_validation)
        except DjangoValidationError as e:
            raise DRFValidationError(detail=serializers.as_serializer_error(e))
        return data
