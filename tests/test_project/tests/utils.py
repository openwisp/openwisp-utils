import json
import os
import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from openwisp_utils.test_selenium_mixins import (
    SeleniumTestMixin as BaseSeleniumTestMixin,
)
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

User = get_user_model()


class TestConfigMixin(object):
    """
    Get the configurations that are to be used for all the tests.
    """

    config_file = os.path.join(os.path.dirname(__file__), 'config.json')
    root_location = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
    with open(config_file) as json_file:
        config = json.load(json_file)


class SeleniumTestMixin(BaseSeleniumTestMixin, TestConfigMixin):
    def _create_user(self, **kwargs):
        opts = dict(
            username=self.config['tester_username'],
            password=self.config['tester_password'],
            first_name=self.config['tester_first_name'],
            last_name=self.config['tester_last_name'],
            email=self.config['tester_email'],
        )
        opts.update(kwargs)
        user = User(**opts)
        user.full_clean()
        return User.objects.create_user(**opts)

    def _create_admin(self, **kwargs):
        opts = dict(
            username=self.config['admin_username'],
            email=self.config['admin_email'],
            password=self.config['admin_password'],
            is_superuser=True,
            is_staff=True,
        )
        opts.update(kwargs)
        return self._create_user(**opts)

    def logout(self):
        account_button = self._get_account_button()
        account_button.click()
        logout_link = self._get_logout_link()
        logout_link.click()

    def _get_menu_toggle(self):
        return self.web_driver.find_element(By.CSS_SELECTOR, '.menu-toggle')

    def _get_menu(self):
        return self.web_driver.find_element(By.ID, 'menu')

    def _get_nav(self):
        return self.web_driver.find_element(By.CSS_SELECTOR, '#menu .nav')

    def _get_hamburger(self):
        return self.web_driver.find_element(By.CSS_SELECTOR, '.hamburger')

    def _get_main_content(self):
        return self.web_driver.find_element(By.ID, 'main-content')

    def _get_menu_home_item_label(self):
        return self.web_driver.find_element(
            By.CSS_SELECTOR, 'a.menu-item:nth-child(1) > span:nth-child(2)'
        )

    def _get_logo(self):
        return self.web_driver.find_element(By.ID, 'site-name')

    def _get_container(self):
        return self.web_driver.find_element(By.ID, 'container')

    def _get_test_mg_head(self):
        return self.web_driver.find_element(By.CSS_SELECTOR, '#mg-control-32')

    def _get_test_mg_icon(self):
        return self.web_driver.find_element(By.CSS_SELECTOR, '.auth')

    def _get_test_mg_label(self):
        return self.web_driver.find_element(
            By.CSS_SELECTOR, '#mg-control-32 > div:nth-child(1) > span:nth-child(2)'
        )

    def _get_active_mg(self):
        return self.web_driver.find_element(By.CSS_SELECTOR, '.active-mg .mg-dropdown')

    def _get_active_mg_head(self):
        return self.web_driver.find_element(By.CSS_SELECTOR, '.active-mg .mg-head')

    def _get_test_mg_dropdown(self):
        return self.web_driver.find_element(By.CSS_SELECTOR, '#mg-dropdown-32')

    def _get_test_mg_dropdown_label(self):
        return self.web_driver.find_element(
            By.CSS_SELECTOR, '#mg-dropdown-32 > div:nth-child(1)'
        )

    def _get_account_button(self):
        return self.web_driver.find_element(By.CSS_SELECTOR, '.account-button')

    def _get_account_dropdown(self):
        return self.web_driver.find_element(By.CSS_SELECTOR, '.account-menu')

    def _get_account_button_username(self):
        return self.web_driver.find_element(By.CSS_SELECTOR, '.account-button strong')

    def _get_account_dropdown_username(self):
        return self.web_driver.find_element(By.CSS_SELECTOR, '.account-menu-username')

    def _get_logout_link(self):
        return self.web_driver.find_element(By.CSS_SELECTOR, '.menu-link')

    def _get_menu_backdrop(self):
        return self.web_driver.find_element(By.CSS_SELECTOR, '.menu-backdrop')

    def _get_simple_input_filter(self):
        return self.web_driver.find_element(By.CSS_SELECTOR, 'input[name=shelf]')

    def _get_input_filter(self):
        return self.web_driver.find_element(
            By.CSS_SELECTOR, 'input[name=books_type__exact]'
        )

    def _open_menu(self):
        hamburger = self._get_hamburger()
        if not hamburger.is_displayed():
            hamburger = self._get_menu_toggle()
        container = self._get_container()
        container_classes = container.get_attribute('class').split()
        for class_name in container_classes:
            if class_name == 'toggle-menu':
                hamburger.click()

    def _close_menu(self):
        hamburger = self._get_hamburger()
        if not hamburger.is_displayed():
            hamburger = self._get_menu_toggle()
        container = self._get_container()
        is_menu_close = False
        container_classes = container.get_attribute('class').split()
        for class_name in container_classes:
            if class_name == 'toggle-menu':
                is_menu_close = True
        if not is_menu_close:
            hamburger.click()

    def _get_filter(self):
        return self.web_driver.find_element(By.ID, 'ow-changelist-filter')

    def _get_filter_button(self):
        return self.web_driver.find_element(By.ID, 'ow-apply-filter')

    def _get_clear_button(self):
        return self.web_driver.find_element(By.ID, 'changelist-filter-clear')

    def check_exists_by_id(self, id):
        try:
            self.web_driver.find_element(By.ID, id)
        except NoSuchElementException:
            return False
        return True

    def check_exists_by_xpath(self, xpath):
        try:
            self.web_driver.find_element(By.XPATH, xpath)
        except NoSuchElementException:
            return False
        return True

    def check_exists_by_css_selector(self, selector):
        try:
            self.web_driver.find_element(By.CSS_SELECTOR, selector)
        except NoSuchElementException:
            return False
        return True

    def _get_filter_selected_option(self, filter_class):
        return self.web_driver.find_element(
            By.CSS_SELECTOR, f'.{filter_class} .selected-option'
        )

    def _get_filter_dropdown(self, filter_class):
        return self.web_driver.find_element(
            By.CSS_SELECTOR, f'.{filter_class} .filter-options'
        )

    def _get_filter_title(self, filter_class):
        return self.web_driver.find_element(
            By.CSS_SELECTOR, f'.{filter_class} .filter-title'
        )

    def _get_filter_anchor(self, query):
        return self.web_driver.find_element(By.XPATH, f'//a[@href="?{query}"]')

    def wait_for_dropdown(self, filter_class):
        WebDriverWait(self.web_driver, 2).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, f'.{filter_class} .filter-options')
            )
        )


class MockUser:
    def __init__(self, is_superuser=False):
        self.is_superuser = is_superuser
        self.id = uuid.uuid4()


class MockRequest:
    def __init__(self, user=None):
        if user:
            self.user = user
        else:
            self.user = AnonymousUser()
