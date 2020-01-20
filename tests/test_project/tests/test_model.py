from django.core.exceptions import ValidationError
from django.test import TestCase

from ..models import Project


class TestModel(TestCase):
    TEST_KEY = 'w1gwJxKaHcamUw62TQIPgYchwLKn3AA0'

    def test_key_validator(self):
        p = Project.objects.create(name='test_project')
        p.key = 'key/key'
        with self.assertRaises(ValidationError):
            p.full_clean()
        p.key = 'key.key'
        with self.assertRaises(ValidationError):
            p.full_clean()
        p.key = 'key key'
        with self.assertRaises(ValidationError):
            p.full_clean()
        p.key = self.TEST_KEY
        p.full_clean()
