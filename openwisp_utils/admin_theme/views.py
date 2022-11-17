from admin_auto_filters.views import AutocompleteJsonView as BaseAutocompleteJsonView
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse


class AutocompleteJsonView(BaseAutocompleteJsonView):
    admin_site = None

    def get(self, request, *args, **kwargs):
        (
            self.term,
            self.model_admin,
            self.source_field,
            _,
        ) = self.process_request(request)

        if not self.has_perm(request):
            raise PermissionDenied

        self.support_reverse_relation()
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        # Add option for filtering objects with None field.
        results = []
        if not self.term or self.term == '-':
            results += [{'id': 'null', 'text': '-'}]
        results += [
            {'id': str(obj.pk), 'text': self.display_text(obj)}
            for obj in context['object_list']
        ]
        return JsonResponse(
            {
                'results': results,
                'pagination': {'more': context['page_obj'].has_next()},
            }
        )

    def support_reverse_relation(self):
        if not hasattr(self.source_field, 'get_limit_choices_to'):

            def get_choices_mock():
                return {}

            self.source_field.get_limit_choices_to = get_choices_mock
