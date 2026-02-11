from dalf.admin import DALFRelatedFieldAjax as BaseAutocompleteFilter
from django.contrib import messages
from django.contrib.admin.filters import FieldListFilter, SimpleListFilter
from django.contrib.admin.utils import NotRelationField, get_model_from_relation
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db.models.fields import CharField, UUIDField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class InputFilterMixin:
    template = "admin/input_filter.html"

    def lookups(self, request, model_admin):
        # Required to show the filter.
        return [tuple()]

    def choices(self, changelist):
        all_choice = {
            "selected": self.value() is None,
            "query_string": changelist.get_query_string(remove=[self.parameter_name]),
            "display": _("All"),
            "query_parts": [],
        }
        for key, value in changelist.get_filters_params().items():
            if key != self.parameter_name:
                all_choice["query_parts"].append((key, value))
        yield all_choice

    def value(self):
        """Returns the querystring for this filter

        If no querystring was supllied, will return None.
        """
        return self.used_parameters.get(self.parameter_name)


class SimpleInputFilter(InputFilterMixin, SimpleListFilter):
    def queryset(self, request, queryset):
        raise NotImplementedError


class InputFilter(InputFilterMixin, FieldListFilter):
    parameter_name = None
    lookup = "exact"
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
                    f"field of Input filter must be a type of {self.allowed_fields}"
                )
            self.lookup_kwarg = "%s__%s" % (
                field_path,
                field.target_field.name,
            )
            if self.lookup:
                self.lookup_kwarg += "__%s" % self.lookup
        else:
            if not isinstance(field, self.allowed_fields):
                raise ImproperlyConfigured(
                    f"field of Input filter must be a type of {self.allowed_fields}"
                )
            self.lookup_kwarg = "%s" % (field_path)
            if self.lookup:
                self.lookup_kwarg += "__%s" % self.lookup
        if not self.parameter_name:
            self.parameter_name = self.lookup_kwarg
        self.lookup_kwarg_isnull = "%s__isnull" % field_path
        self.lookup_val = params.get(self.lookup_kwarg)
        self.lookup_val_isnull = params.get(self.lookup_kwarg_isnull)
        super().__init__(field, request, params, model, model_admin, field_path)
        if hasattr(field, "verbose_name"):
            self.lookup_title = field.verbose_name
        elif other_model:
            self.lookup_title = other_model._meta.verbose_name
        self.title = self.lookup_title
        self.empty_value_display = model_admin.get_empty_value_display()

    def expected_parameters(self):
        return [self.lookup_kwarg, self.lookup_kwarg_isnull]


class AutocompleteFilter(BaseAutocompleteFilter):
    template = "admin/auto_filter.html"
    widget_attrs = {
        "data-dropdown-css-class": "ow2-autocomplete-dropdown",
        "data-empty-label": "-",
    }

    class Media:
        css = {
            "screen": (
                "admin/css/vendor/select2/select2.css",
                "admin/css/autocomplete.css",
                "admin/css/ow-auto-filter.css",
            ),
        }
        js = (
            # 1. Django's Setup 
            "admin/js/jquery.init.js",
            
            # 2. Django's Autocomplete Logic
            "admin/js/autocomplete.js",
            
            # 3. The Library Script 
            "admin/js/django_admin_list_filter.js",
            
            # 4. OpenWISP's Custom Script
            "admin/js/ow-auto-filter.js",
        )

    def __init__(self, field, request, params, model, model_admin, field_path):
        # We manually use the full arguments instead of *args, **kwargs
        # so we can manipulate self.ajax_url after initialization
        try:
            super().__init__(field, request, params, model, model_admin, field_path)
            # Override dalf's default URL to use OpenWISP's custom view
            self.ajax_url = reverse("admin:ow-auto-filter")
        except (ValidationError, ValueError):
            # Handle invalid UUIDs passed in params during init
            pass

    def value(self):
        """
        Returns the value of this filter from the query string.
        Required for the 'choices' method to determine if 'All' is selected.
        """
        return self.used_parameters.get(self.lookup_kwarg)

    def choices(self, changelist):
        all_choice = {
            "selected": self.value() is None,
            "query_string": changelist.get_query_string(remove=[self.parameter_name]),
            "display": _("All"),
            "query_parts": [],
            "parameter_name": self.lookup_kwarg,
    }

        for key, value in changelist.get_filters_params().items():
            if key != self.parameter_name:
                all_choice["query_parts"].append((key, value))

        yield all_choice


    def queryset(self, request, queryset):
        """
        Fixes AssertionError: 302 != 200.
        Catches validation errors (like invalid UUIDs) and displays a message
        instead of crashing or redirecting.
        """
        try:
            return super().queryset(request, queryset)
        except (ValidationError, ValueError) as e:
            if hasattr(e, "messages"):
                error_msg = " ".join(e.messages)
            else:
                error_msg = str(e)
            messages.error(request, error_msg)
            return queryset