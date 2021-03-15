from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase
from test_project.serializers import ShelfSerializer

from ..models import Shelf
from . import CreateMixin


class TestApi(CreateMixin, TestCase):
    shelf_model = Shelf
    operator_permission_filter = [{'codename__endswith': 'shelf'}]

    def test_validator_pass(self):
        s1 = self._create_shelf(name='shelf1')
        serializer = ShelfSerializer(s1)
        result = serializer.validate(s1)
        self.assertIsInstance(result, Shelf)

    def test_validator_fail(self):
        with self.assertRaises(ValidationError):
            self._create_shelf(name='Intentional_Test_Fail')

    def test_rest_framework_settings_override(self):
        drf_conf = getattr(settings, 'REST_FRAMEWORK', {})
        self.assertEqual(
            drf_conf,
            {
                'DEFAULT_THROTTLE_CLASSES': [
                    'test_project.api.throttling.CustomScopedRateThrottle'
                ],
                'DEFAULT_THROTTLE_RATES': {'anon': '20/hour', 'test': '10/minute'},
                'TEST': True,
            },
        )
