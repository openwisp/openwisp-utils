from django.core.exceptions import ValidationError
from django.test import TestCase
from openwisp_users.tests.utils import TestOrganizationMixin
from test_project.serializers import ShelfSerializer

from . import CreateMixin
from ..models import Shelf


class TestApi(CreateMixin, TestOrganizationMixin, TestCase):
    shelf_model = Shelf
    operator_permission_filter = [
        {'codename__endswith': 'shelf'},
    ]

    def test_validator_pass(self):
        org1 = self._create_org(name='org1')
        s1 = self._create_shelf(name='shelf1', organization=org1)
        serializer = ShelfSerializer(s1)
        result = serializer.validate(s1)
        self.assertIsInstance(result, Shelf)

    def test_validator_fail(self):
        org1 = self._create_org(name='org1')
        with self.assertRaises(ValidationError):
            self._create_shelf(name='Intentional_Test_Fail', organization=org1)
