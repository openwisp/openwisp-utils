import json
import os

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

User = get_user_model()


class TestConfig(object):
    """
    Get the configurations that are to be used for all the tests.
    """

    config_file = os.path.join(os.path.dirname(__file__), 'config.json')
    root_location = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
    with open(config_file) as json_file:
        config = json.load(json_file)


class SeleniumTestCase(StaticLiveServerTestCase, TestConfig):
    def open(self, url, driver=None):
        """
        Opens a URL
        Argument:
            url: URL to open
            driver: selenium driver (default: cls.base_driver)
        """
        if not driver:
            driver = self.web_driver
        driver.get(f'{self.live_server_url}{url}')

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

    def login(self, username=None, password=None, driver=None):
        """
        Log in to the admin dashboard
        Argument:
            driver: selenium driver (default: cls.web_driver)
            username: username to be used for login (default: cls.admin.username)
            password: password to be used for login (default: cls.admin.password)
        """
        if not driver:
            driver = self.web_driver
        if not username:
            username = self.config['admin_username']
        if not password:
            password = self.config['admin_password']
        url = self.live_server_url + self.config['login_url']
        driver.get(url)
        if 'admin/login' in driver.current_url:
            driver.find_element_by_name('username').send_keys(username)
            driver.find_element_by_name('password').send_keys(password)
            driver.find_element_by_xpath('//input[@type="submit"]').click()

    def logout(self):
        account_button = self._get_account_button()
        account_button.click()
        logout_link = self._get_logout_link()
        logout_link.click()

    def _get_menu_toggle(self):
        return self.web_driver.find_element_by_css_selector('.menu-toggle')

    def _get_menu(self):
        return self.web_driver.find_element_by_id('menu')

    def _get_nav(self):
        return self.web_driver.find_element_by_css_selector('#menu .nav')

    def _get_hamburger(self):
        return self.web_driver.find_element_by_css_selector('.hamburger')

    def _get_main_content(self):
        return self.web_driver.find_element_by_id('main-content')

    def _get_menu_home_item_label(self):
        # TODO: CHange name
        return self.web_driver.find_element_by_xpath(
            '//span[@class="label" and contains(.,"Home")]'
        )

    def _get_logo(self):
        return self.web_driver.find_element_by_id('site-name')

    def _get_container(self):
        return self.web_driver.find_element_by_id('container')

    def _get_test_mg_head(self):
        return self.web_driver.find_element_by_xpath('//*[@class="nav"]/div[1]/div[1]')

    def _get_test_mg_icon(self):
        return self.web_driver.find_element_by_xpath(
            '//*[@class="nav"]/div[1]/div[1]/div[1]/span[1]'
        )

    def _get_test_mg_label(self):
        return self.web_driver.find_element_by_xpath(
            '//*[@class="nav"]/div[1]/div[1]/div[1]/span[2]'
        )

    def _get_active_mg(self):
        return self.web_driver.find_element_by_css_selector('.active-mg .mg-dropdown')

    def _get_active_mg_head(self):
        return self.web_driver.find_element_by_css_selector('.active-mg .mg-head')

    def _get_test_mg_dropdown(self):
        return self.web_driver.find_element_by_xpath('//*[@class="nav"]/div[1]/div[2]')

    def _get_test_mg_dropdown_label(self):
        return self.web_driver.find_element_by_xpath(
            '//*[@class="nav"]/div[1]/div[2]/div[1]'
        )

    def _get_account_button(self):
        return self.web_driver.find_element_by_css_selector('.account-button')

    def _get_account_dropdown(self):
        return self.web_driver.find_element_by_css_selector('.account-menu')

    def _get_account_button_username(self):
        return self.web_driver.find_element_by_css_selector('.account-button strong')

    def _get_account_dropdown_username(self):
        return self.web_driver.find_element_by_css_selector('.account-menu-username')

    def _get_logout_link(self):
        return self.web_driver.find_element_by_xpath(
            '//a[@class="menu-link" and @href="/admin/logout/"]'
        )

    def _get_menu_backdrop(self):
        return self.web_driver.find_element_by_css_selector('.menu-backdrop')

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
