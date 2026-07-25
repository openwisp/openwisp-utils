from importlib import reload

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from openwisp_utils import settings as app_settings
from openwisp_utils.api import pagination as pagination_module
from openwisp_utils.api.pagination import OpenWispPagination
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from test_project.serializers import ShelfSerializer

from ..models import Shelf
from . import CreateMixin


class TestApi(CreateMixin, TestCase):
    shelf_model = Shelf
    operator_permission_filter = [{"codename__endswith": "shelf"}]

    def test_validator_data_dict(self):
        s1 = self._create_shelf(name="shelf1")
        data = s1.__dict__.copy()
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
        serializer = ShelfSerializer(instance=s1, data=data)
        data = serializer.validate(data)

    def test_validator_fail(self):
        with self.assertRaises(DjangoValidationError):
            self._create_shelf(name="Intentional_Test_Fail")

        s1 = self._create_shelf(name="shelf1")
        with self.assertRaises(DRFValidationError):
            serializer = ShelfSerializer(instance=s1)
            serializer.validate({"name": "Intentional_Test_Fail"})

    def test_exclude_validation(self):
        s1 = self._create_shelf(name="shelf1")
        with self.assertRaises(DRFValidationError):
            serializer = ShelfSerializer(instance=s1)
            serializer.validate({"books_type": "invalid"})
        serializer = ShelfSerializer(instance=s1)
        serializer.exclude_validation = ["books_type"]
        serializer.validate({"books_type": "invalid"})

    def test_nested_relation_validation_data_is_not_assigned_directly(self):
        class OwnerSerializer(serializers.ModelSerializer):
            class Meta:
                model = get_user_model()
                fields = ["username"]

        class NestedShelfSerializer(ShelfSerializer):
            owner = OwnerSerializer()

            class Meta(ShelfSerializer.Meta):
                fields = ["name", "owner"]

        s1 = self._create_shelf(name="shelf1")
        data = {"owner": {"username": "alice"}}
        serializer = NestedShelfSerializer(instance=s1)
        self.assertEqual(serializer.validate(data), data)

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

    def test_crud_shelf(self):
        list_url = reverse("shelf_list")
        with self.subTest("Create"):
            response = self.client.post(
                list_url,
                {
                    "name": "Fiction Shelf",
                    "books_type": "FANTASY",
                    "books_count": 3,
                    "locked": False,
                },
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Shelf.objects.count(), 1)
            pk = response.data["id"]

        shelf = Shelf.objects.get(pk=pk)
        detail_url = reverse("shelf_detail", args=[pk])
        with self.subTest("List"):
            response = self.client.get(list_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["results"][0]["id"], pk)

        with self.subTest("Retrieve"):
            response = self.client.get(detail_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["id"], pk)

        with self.subTest("Update with PATCH"):
            response = self.client.patch(
                detail_url,
                {"name": "Shelf - Updated"},
                content_type="application/json",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            shelf.refresh_from_db()
            self.assertEqual(shelf.name, "Shelf - Updated")

        with self.subTest("Update with PUT"):
            payload = {
                "name": "Shelf PUT Full",
                "books_type": "FACTUAL",
                "books_count": 5,
                "locked": False,
            }
            response = self.client.put(
                detail_url, payload, content_type="application/json"
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            shelf.refresh_from_db()
            self.assertEqual(shelf.name, "Shelf PUT Full")

        with self.subTest("Delete"):
            response = self.client.delete(detail_url)
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            self.assertEqual(Shelf.objects.count(), 0)

    def test_model_validation_create_and_update(self):
        list_url = reverse("shelf_list")
        with self.subTest("Create (invalid)"):
            response = self.client.post(
                list_url, {"name": "Intentional_Test_Fail"}, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with self.subTest("Create (valid)"):
            response = self.client.post(
                list_url,
                {
                    "name": "Reference Shelf",
                    "books_type": "FACTUAL",
                    "books_count": 7,
                    "locked": True,
                },
                content_type="application/json",
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            pk = response.data["id"]

        detail_url = reverse("shelf_detail", args=[pk])
        with self.subTest("Update - PATCH (invalid)"):
            response = self.client.patch(
                detail_url,
                {"name": "Intentional_Test_Fail"},
                content_type="application/json",
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with self.subTest("Update - PUT (valid)"):
            payload = {
                "name": "Valid PUT Shelf",
                "books_type": "FACTUAL",
                "books_count": 10,
                "locked": True,
            }
            response = self.client.put(
                detail_url, payload, content_type="application/json"
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        with self.subTest("Update - PUT (invalid)"):
            invalid_payload = {
                "name": "Intentional_Test_Fail",
                "books_type": "FACTUAL",
                "books_count": 7,
                "locked": True,
            }
            response = self.client.put(
                detail_url, invalid_payload, content_type="application/json"
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("Intentional_Test_Fail", str(response.data))
            self.assertNotIn("This field is required", str(response.data))

        with self.subTest("DB value unchanged after failed updates"):
            shelf = Shelf.objects.get(pk=pk)
            self.assertEqual(shelf.name, "Valid PUT Shelf")
            self.assertEqual(shelf.books_count, 10)
            self.assertEqual(shelf.locked, True)


class TestOpenWispPagination(CreateMixin, TestCase):
    shelf_model = Shelf

    def setUp(self):
        super().setUp()
        self.url = "/api/v1/shelves/"
        # Create 21 shelves to test pagination across multiple pages
        for i in range(21):
            self._create_shelf(name=f"shelf{i}")

    def test_list_shelf_api_pagination(self):
        number_of_shelves = 21
        default_page_size = app_settings.API_DEFAULT_PAGE_SIZE
        last_page_size = number_of_shelves % default_page_size
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], number_of_shelves)
        self.assertIsNotNone(response.data["next"])
        self.assertIn("page=2", response.data["next"])
        self.assertIsNone(response.data["previous"])
        self.assertEqual(len(response.data["results"]), default_page_size)

        next_response = self.client.get(response.data["next"])
        self.assertEqual(next_response.status_code, 200)
        self.assertEqual(next_response.data["count"], number_of_shelves)
        self.assertIsNotNone(next_response.data["next"])
        self.assertIn("page=3", next_response.data["next"])
        self.assertIsNotNone(next_response.data["previous"])
        # Page 1 is the default, so DRF doesn't include page=1 in the previous URL
        self.assertIn(self.url, next_response.data["previous"])
        self.assertEqual(len(next_response.data["results"]), default_page_size)

        third_response = self.client.get(next_response.data["next"])
        self.assertEqual(third_response.status_code, 200)
        self.assertEqual(third_response.data["count"], number_of_shelves)
        self.assertIsNone(third_response.data["next"])
        self.assertIsNotNone(third_response.data["previous"])
        self.assertIn("page=2", third_response.data["previous"])
        self.assertEqual(len(third_response.data["results"]), last_page_size)

    def test_list_shelf_api_custom_page_size(self):
        number_of_shelves = 21
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
        # Page 1 is the default, so DRF doesn't include page=1 in the previous URL
        self.assertIn(url_with_page_size, next_response.data["previous"])
        self.assertEqual(len(next_response.data["results"]), page_size)

        # Walk to the last page to verify the partial-page boundary
        last_response = next_response
        while last_response.data["next"] is not None:
            last_response = self.client.get(last_response.data["next"])
            self.assertEqual(last_response.status_code, 200)
        self.assertEqual(last_response.data["count"], number_of_shelves)
        self.assertEqual(len(last_response.data["results"]), 1)
        self.assertIsNone(last_response.data["next"])
        self.assertIsNotNone(last_response.data["previous"])
        self.assertIn("page=4", last_response.data["previous"])
        self.assertIn(f"page_size={page_size}", last_response.data["previous"])

    def test_pagination_attributes(self):
        pagination = OpenWispPagination()
        self.assertIsInstance(pagination, PageNumberPagination)
        self.assertEqual(pagination.page_size, app_settings.API_DEFAULT_PAGE_SIZE)
        self.assertEqual(pagination.max_page_size, app_settings.API_MAX_PAGE_SIZE)
        self.assertEqual(pagination.page_size_query_param, "page_size")

    def _reload_pagination_settings(self):
        reload(app_settings)
        reload(pagination_module)
        return pagination_module.OpenWispPagination

    def test_pagination_attributes_can_be_overridden(self):
        try:
            with override_settings(
                OPENWISP_API_DEFAULT_PAGE_SIZE=7,
                OPENWISP_API_MAX_PAGE_SIZE=8,
            ):
                Pagination = self._reload_pagination_settings()
                pagination = Pagination()
                queryset = Shelf.objects.order_by("id")
                factory = APIRequestFactory()
                # test custom default page size
                request = Request(factory.get(self.url))
                paginated = pagination.paginate_queryset(queryset, request)
                self.assertEqual(pagination.page_size, 7)
                self.assertEqual(len(paginated), 7)
                # test custom max page size
                request = Request(factory.get(self.url, {"page_size": 50}))
                paginated = pagination.paginate_queryset(queryset, request)
                self.assertEqual(pagination.max_page_size, 8)
                self.assertEqual(len(paginated), 8)
        # restore default settings
        finally:
            self._reload_pagination_settings()

    def test_pagination_page_size_can_be_overridden_by_view(self):
        class View:
            pagination_page_size = 20

        pagination = OpenWispPagination()
        queryset = Shelf.objects.order_by("id")
        factory = APIRequestFactory()
        request = Request(factory.get(self.url))
        paginated = pagination.paginate_queryset(queryset, request, view=View())
        self.assertEqual(len(paginated), 20)
        request = Request(factory.get(self.url, {"page_size": 5}))
        paginated = pagination.paginate_queryset(queryset, request, view=View())
        self.assertEqual(len(paginated), 5)

    def test_list_shelf_api_page_size_capped_at_max(self):
        max_page_size = OpenWispPagination.max_page_size
        # Create enough shelves so the response would exceed max_page_size
        # if the cap were not enforced.
        extra = (max_page_size + 5) - Shelf.objects.count()
        for i in range(extra):
            self._create_shelf(name=f"extra_shelf{i}")
        total = Shelf.objects.count()
        self.assertGreater(total, max_page_size)

        response = self.client.get(f"{self.url}?page_size={max_page_size + 50}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], total)
        self.assertEqual(len(response.data["results"]), max_page_size)
