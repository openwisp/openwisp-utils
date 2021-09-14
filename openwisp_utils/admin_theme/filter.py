from django.contrib import admin


class InputFilter(admin.SimpleListFilter):
    template = 'admin/input_filter.html'

    def lookups(self, request, model_admin):
        # Required to show the filter.
        return [tuple()]

    def choices(self, changelist):
        # Grab only the "all" option.
        all_choice = next(super().choices(changelist))
        all_choice['query_parts'] = []
        for key, value in changelist.get_filters_params().items():
            if key != self.parameter_name:
                all_choice['query_parts'].append((key, value))
        yield all_choice
