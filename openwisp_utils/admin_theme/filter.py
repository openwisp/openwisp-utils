from django.contrib.admin.filters import FieldListFilter
from django.contrib.admin.utils import NotRelationField, get_model_from_relation
from django.core.exceptions import ImproperlyConfigured
from django.db.models.fields import CharField, UUIDField
from django.utils.translation import gettext_lazy as _


class InputFilter(FieldListFilter):
    template = 'admin/input_filter.html'
    parameter_name = None
    lookup = 'exact'
    allowed_fields = (CharField, UUIDField)

    def __init__(self, field, request, params, model, model_admin, field_path):
        other_model = None
        target_field = None
        try:
            other_model = get_model_from_relation(field)
        except NotRelationField:
            pass
        try:
            target_field = field.target_field
        except AttributeError:
            pass
        if target_field:
            if not isinstance(target_field, self.allowed_fields):
                raise ImproperlyConfigured(
                    f'field of Input filter must be a type of {self.allowed_fields}'
                )
            self.lookup_kwarg = '%s__%s' % (
                field_path,
                field.target_field.name,
            )
            if self.lookup:
                self.lookup_kwarg += '__%s' % self.lookup
        else:
            if not isinstance(field, self.allowed_fields):
                raise ImproperlyConfigured(
                    f'field of Input filter must be a type of {self.allowed_fields}'
                )
            self.lookup_kwarg = '%s' % (field_path)
            if self.lookup:
                self.lookup_kwarg += '__%s' % self.lookup
        if not self.parameter_name:
            self.parameter_name = self.lookup_kwarg
        self.lookup_kwarg_isnull = '%s__isnull' % field_path
        self.lookup_val = params.get(self.lookup_kwarg)
        self.lookup_val_isnull = params.get(self.lookup_kwarg_isnull)
        super().__init__(field, request, params, model, model_admin, field_path)
        if hasattr(field, 'verbose_name'):
            self.lookup_title = field.verbose_name
        elif other_model:
            self.lookup_title = other_model._meta.verbose_name
        self.title = self.lookup_title
        self.empty_value_display = model_admin.get_empty_value_display()

    def choices(self, changelist):
        all_choice = {
            'selected': self.lookup_val is None,
            'query_string': changelist.get_query_string(
                remove=[self.lookup_kwarg, self.lookup_kwarg_isnull]
            ),
            'display': _('All'),
            'query_parts': [],
            'parameter_name': self.parameter_name,
            'value': self.lookup_val,
        }
        for key, value in changelist.get_filters_params().items():
            if key != self.parameter_name:
                all_choice["query_parts"].append((key, value))
        yield all_choice

    def lookups(self, request, model_admin):
        # Required to show the filter.
        return [tuple()]

    def expected_parameters(self):
        return [self.lookup_kwarg, self.lookup_kwarg_isnull]
