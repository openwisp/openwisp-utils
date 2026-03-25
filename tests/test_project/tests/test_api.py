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
            resp = self.client.post(list_url, {"name": "shelf1"}, format="json")
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Shelf.objects.count(), 1)
            pk = resp.data["id"]

        shelf = Shelf.objects.get(pk=pk)
        detail_url = reverse("shelf_detail", args=[pk])
        with self.subTest("List"):
            resp = self.client.get(list_url)
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            self.assertIn(pk, [s["id"] for s in resp.data])

        with self.subTest("Retrieve"):
            resp = self.client.get(detail_url)
            self.assertEqual(resp.status_code, status.HTTP_200_OK)

        with self.subTest("Update"):
            resp = self.client.patch(
                detail_url, {"name": "shelf2"}, content_type="application/json"
            )
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            # ensure the DB reflects the change
            shelf.refresh_from_db()
            self.assertEqual(shelf.name, "shelf2")

        with self.subTest("Delete"):
            resp = self.client.delete(detail_url)
            self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
            self.assertEqual(Shelf.objects.count(), 0)

    def test_model_validation_create_and_update(self):
        list_url = reverse("shelf_list")
        # Creating with invalid name should fail due to model.clean()
        resp = self.client.post(
            list_url, {"name": "Intentional_Test_Fail"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        # Create valid
        resp = self.client.post(list_url, {"name": "valid"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        pk = resp.data["id"]
        detail_url = reverse("shelf_detail", args=[pk])
        # Updating to invalid should fail
        resp = self.client.patch(
            detail_url,
            {"name": "Intentional_Test_Fail"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        # Ensure DB value unchanged
        shelf = Shelf.objects.get(pk=pk)
        self.assertEqual(shelf.name, "valid")
