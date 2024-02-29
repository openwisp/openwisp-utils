from django.test import TestCase
from django.urls import reverse

from . import AdminTestMixin


class TestIntegrations(AdminTestMixin, TestCase):
    def test_swagger_api_docs(self):
        response = self.client.get(reverse('schema-swagger-ui'), {'format': 'openapi'})
        self.assertEqual(response.status_code, 200)
