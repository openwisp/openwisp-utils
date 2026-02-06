from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase
from openwisp_utils.api.pagination import OpenWispPagination
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from test_project.serializers import ShelfSerializer

from ..models import Shelf
from . import CreateMixin


class TestApi(CreateMixin, TestCase):
    shelf_model = Shelf
    operator_permission_filter = [{"codename__endswith": "shelf"}]

    def test_validator_pass(self):
        s1 = self._create_shelf(name="shelf1")
        serializer = ShelfSerializer(s1)
        result = serializer.validate(s1)
        self.assertIsInstance(result, Shelf)

    def test_validator_data_dict(self):
        s1 = self._create_shelf(name="shelf1")
        data = s1.__dict__
        to_delete = [
            "_state",
            "id",
            "created",
            "created_at",
            "modified",
        ]
        for key in to_delete:
            del data[key]
        data["writers"] = [1]
        serializer = ShelfSerializer()
        data = serializer.validate(data)

    def test_validator_fail(self):
        with self.assertRaises(ValidationError):
            self._create_shelf(name="Intentional_Test_Fail")

        s1 = self._create_shelf(name="shelf1")
        s1.name = "Intentional_Test_Fail"
        serializer = ShelfSerializer(s1)
        with self.assertRaises(ValidationError):
            serializer.validate(s1)

    def test_exclude_validation(self):
        s1 = self._create_shelf(name="shelf1")
        s1.books_type = "madeup"
        serializer = ShelfSerializer(s1)
        with self.assertRaises(ValidationError):
            serializer.validate(s1)
        serializer.exclude_validation = ["books_type"]
        serializer.validate(s1)

    def test_rest_framework_settings_override(self):
        drf_conf = getattr(settings, "REST_FRAMEWORK", {})
        self.assertEqual(
            drf_conf,
            {
                "DEFAULT_THROTTLE_CLASSES": [
                    "test_project.api.throttling.CustomScopedRateThrottle"
                ],
                "DEFAULT_THROTTLE_RATES": {"anon": "20/hour", "test": "10/minute"},
                "TEST": True,
            },
        )


class TestOpenWispPagination(CreateMixin, TestCase):
    shelf_model = Shelf

    def setUp(self):
        self.factory = APIRequestFactory()
        self.pagination = OpenWispPagination()
        for i in range(15):
            self._create_shelf(name=f"shelf{i}")

    def _get_request(self, path="/api/shelves/", data=None):
        return Request(self.factory.get(path, data))

    def test_inheritance(self):
        self.assertIsInstance(self.pagination, PageNumberPagination)

    def test_default_attributes(self):
        self.assertEqual(self.pagination.page_size, 10)
        self.assertEqual(self.pagination.max_page_size, 100)
        self.assertEqual(self.pagination.page_size_query_param, "page_size")

    def test_paginate_queryset(self):
        request = self._get_request()
        queryset = Shelf.objects.all().order_by("id")
        paginated = self.pagination.paginate_queryset(queryset, request)
        self.assertEqual(len(paginated), 10)

    def test_paginate_queryset_second_page(self):
        request = self._get_request(data={"page": 2})
        queryset = Shelf.objects.all().order_by("id")
        paginated = self.pagination.paginate_queryset(queryset, request)
        self.assertEqual(len(paginated), 5)

    def test_paginate_queryset_custom_page_size(self):
        request = self._get_request(data={"page_size": 5})
        queryset = Shelf.objects.all().order_by("id")
        paginated = self.pagination.paginate_queryset(queryset, request)
        self.assertEqual(len(paginated), 5)

    def test_paginate_queryset_respects_max_page_size(self):
        self.pagination.max_page_size = 10
        request = self._get_request(data={"page_size": 100})
        queryset = Shelf.objects.all().order_by("id")
        paginated = self.pagination.paginate_queryset(queryset, request)
        self.assertEqual(len(paginated), 10)

    def test_get_paginated_response(self):
        request = self._get_request()
        queryset = Shelf.objects.all().order_by("id")
        self.pagination.paginate_queryset(queryset, request)
        response = self.pagination.get_paginated_response([])
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 15)
