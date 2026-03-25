from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
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
        serializer = ShelfSerializer(
            instance=s1, data={"name": "Intentional_Test_Fail"}
        )
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_exclude_validation(self):
        s1 = self._create_shelf(name="shelf1")
        serializer = ShelfSerializer(instance=s1, data={"books_type": "invalid"})
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)
        serializer.exclude_validation = ["books_type"]

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
            self.assertEqual(response.data[0]["id"], pk)

        with self.subTest("Retrieve"):
            response = self.client.get(detail_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["id"], pk)

        with self.subTest("Update with PATCH"):
            response = self.client.patch(
                detail_url, {"name": "Shelf - Updated"}, content_type="application/json"
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # ensure the DB reflects the change
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
            invalid_payload = {"books_count": 7}
            response = self.client.put(
                detail_url, invalid_payload, content_type="application/json"
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with self.subTest("DB value unchanged after failed updates"):
            shelf = Shelf.objects.get(pk=pk)
            self.assertEqual(shelf.name, "Valid PUT Shelf")
            self.assertEqual(shelf.books_count, 10)
            self.assertEqual(shelf.locked, True)
