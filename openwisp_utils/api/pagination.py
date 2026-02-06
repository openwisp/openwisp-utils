from django.core.exceptions import ImproperlyConfigured

try:
    from rest_framework.pagination import PageNumberPagination
except ImportError:  # pragma: nocover
    raise ImproperlyConfigured(
        "Django REST Framework is required to use "
        "this feature but it is not installed"
    )


class OpenWispPagination(PageNumberPagination):
    """Reusable pagination class with sensible defaults."""

    page_size = 10
    max_page_size = 100
    page_size_query_param = "page_size"
