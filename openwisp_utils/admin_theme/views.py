from django.contrib.admin.views.autocomplete import (
    AutocompleteJsonView as DjangoAutocompleteJsonView,
)
from django.db.models.fields.reverse_related import ManyToOneRel


class AutocompleteJsonView(DjangoAutocompleteJsonView):

    def get_queryset(self):
        """Override to support reverse relations without get_limit_choices_to()."""
        # Handle reverse relations (ManyToOneRel) that don't have get_limit_choices_to
        if isinstance(self.source_field, ManyToOneRel) or not hasattr(
            self.source_field, "get_limit_choices_to"
        ):
            # Mock the method for reverse relations
            self.source_field.get_limit_choices_to = lambda: {}
        return super().get_queryset()
