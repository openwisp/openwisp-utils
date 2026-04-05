from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase
from openwisp_utils.api.pagination import OpenWispPagination
from rest_framework.pagination import PageNumberPagination
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
        super().setUp()
        self.url = "/api/v1/shelves/"
        # Create 21 shelves to test pagination across multiple pages
        for i in range(21):
            self._create_shelf(name=f"shelf{i}")

    def test_list_shelf_api(self):
        """Test shelf list API with pagination."""
        number_of_shelves = 21

        with self.subTest('Test "page" query in shelf list view'):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["count"], number_of_shelves)
            self.assertIsNotNone(response.data["next"])
            self.assertIn("page=2", response.data["next"])
            self.assertIsNone(response.data["previous"])
            self.assertEqual(len(response.data["results"]), 10)
            next_response = self.client.get(response.data["next"])
            self.assertEqual(next_response.status_code, 200)
            self.assertEqual(next_response.data["count"], number_of_shelves)
            self.assertIsNotNone(next_response.data["next"])
            self.assertIn("page=3", next_response.data["next"])
            self.assertIsNotNone(next_response.data["previous"])
            self.assertIn("page=1", next_response.data["previous"])
            self.assertEqual(len(next_response.data["results"]), 10)
            third_response = self.client.get(next_response.data["next"])
            self.assertEqual(third_response.status_code, 200)
            self.assertEqual(third_response.data["count"], number_of_shelves)
            self.assertIsNone(third_response.data["next"])
            self.assertIsNotNone(third_response.data["previous"])
            self.assertIn("page=2", third_response.data["previous"])
            self.assertEqual(len(third_response.data["results"]), 1)
        with self.subTest('Test "page_size" query'):
            page_size = 5
            url_with_page_size = f"{self.url}?page_size={page_size}"
            response = self.client.get(url_with_page_size)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["count"], number_of_shelves)
            self.assertIsNotNone(response.data["next"])
            self.assertIn(f"page_size={page_size}", response.data["next"])
            self.assertIn("page=2", response.data["next"])
            self.assertIsNone(response.data["previous"])
            self.assertEqual(len(response.data["results"]), page_size)
            next_response = self.client.get(response.data["next"])
            self.assertEqual(next_response.status_code, 200)
            self.assertEqual(next_response.data["count"], number_of_shelves)
            self.assertIsNotNone(next_response.data["next"])
            self.assertIn(f"page_size={page_size}", next_response.data["next"])
            self.assertIn("page=3", next_response.data["next"])
            self.assertIsNotNone(next_response.data["previous"])
            self.assertIn(f"page_size={page_size}", next_response.data["previous"])
            self.assertIn("page=1", next_response.data["previous"])
            self.assertEqual(len(next_response.data["results"]), page_size)

    def test_pagination_attributes(self):
        """Test OpenWispPagination class attributes."""
        pagination = OpenWispPagination()
        self.assertIsInstance(pagination, PageNumberPagination)
        self.assertEqual(pagination.page_size, 10)
        self.assertEqual(pagination.max_page_size, 100)
        self.assertEqual(pagination.page_size_query_param, "page_size")
