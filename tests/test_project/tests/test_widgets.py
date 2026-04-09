from channels.testing import ChannelsLiveServerTestCase
from django.test import TestCase, tag
from django.urls import reverse
from openwisp_utils.widgets import Select2Widget
from selenium.webdriver.common.by import By

from ..models import Shelf
from .utils import SeleniumTestMixin


class TestWidgets(TestCase):
    def test_select2_widget_attrs(self):
        widget = Select2Widget()
        html = widget.render("name", "value")
        self.assertIn('class="ow-select2"', html)

        # test overriding works and class is preserved
        widget = Select2Widget(attrs={"class": "my-class"})
        html = widget.render("name", "value")
        self.assertIn("ow-select2 my-class", html)

    def test_select2_widget_media(self):
        widget = Select2Widget()
        media = str(widget.media)
        self.assertIn("admin/css/vendor/select2/select2", media)
        self.assertIn("admin/js/vendor/jquery/jquery", media)
        self.assertIn("admin/js/vendor/select2/select2.full", media)
        self.assertIn("openwisp-utils/js/select2.js", media)


@tag("selenium_tests")
class TestSelect2AdminMixinSelenium(SeleniumTestMixin, ChannelsLiveServerTestCase):
    def setUp(self):
        super().setUp()
        self.login()

    def test_select2_widget_renders_on_shelf_add_form(self):
        url = reverse("admin:test_project_shelf_add")
        self.open(url)
        self.wait_for_presence(By.CSS_SELECTOR, "select#id_books_type.ow-select2")

    def test_select2_widget_renders_on_shelf_change_form(self):
        shelf = Shelf.objects.create(name="Test Shelf", books_type="HORROR")
        url = reverse("admin:test_project_shelf_change", args=[shelf.pk])
        self.open(url)
        self.wait_for_presence(By.CSS_SELECTOR, "select#id_books_type.ow-select2")
        self.wait_for_presence(By.CSS_SELECTOR, ".select2-container")
