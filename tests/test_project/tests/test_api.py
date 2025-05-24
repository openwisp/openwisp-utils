from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase
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
