from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
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
        Model = self.Meta.model
        is_update = bool(instance)
        # if instance is empty (eg: creation)
        # simulate for validation purposes
        if not is_update:
            instance = Model()
        else:
            # snapshot the state of the DB instance so it can be
            # restored if validation fails
            original_state = instance.__dict__.copy()
        assignable = {}
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
            assignable[key] = value
        for key, value in assignable.items():
            setattr(instance, key, value)
        # perform model validation
        try:
            instance.full_clean(exclude=self.exclude_validation)
        except DjangoValidationError as e:
            if is_update:
                # validation failed, restore the DB instance to its
                # pre-validation state
                instance.__dict__.update(original_state)
            raise DRFValidationError(detail=serializers.as_serializer_error(e))
        # propagate corrections made by Model.clean() into the validated
        # data, so they reach the instance that gets saved (#760)
        for key in assignable:
            data[key] = getattr(instance, key)
        return data
