from django.core.exceptions import ImproperlyConfigured

from .. import settings as app_settings

try:
    from rest_framework.pagination import PageNumberPagination
except ImportError:  # pragma: nocover
    raise ImproperlyConfigured(
        "Django REST Framework is required to use "
        "this feature but it is not installed"
    )


class OpenWispPagination(PageNumberPagination):
    """Reusable pagination class with settings-backed defaults."""

    page_size = app_settings.API_DEFAULT_PAGE_SIZE
    max_page_size = app_settings.API_MAX_PAGE_SIZE
    page_size_query_param = "page_size"

    def paginate_queryset(self, queryset, request, view=None):
        original_page_size = self.page_size
        self.page_size = getattr(view, "pagination_page_size", self.page_size)
        try:
            return super().paginate_queryset(queryset, request, view=view)
        finally:
            self.page_size = original_page_size
