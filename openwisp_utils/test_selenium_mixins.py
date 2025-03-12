import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class SeleniumTestMixin:
    """A base Mixin Class for Selenium Browser Tests.

    Provides common initialization logic and helper methods like login()
    and open().
    """

    admin_username = 'admin'
    admin_password = 'password'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        firefox_options = Options()
        firefox_options.page_load_strategy = 'eager'
        if os.environ.get('SELENIUM_HEADLESS', False):
            firefox_options.add_argument('--headless')
        GECKO_BIN = os.environ.get('GECKO_BIN', None)
        if GECKO_BIN:
            firefox_options.binary_location = GECKO_BIN
        firefox_options.set_preference(
            'network.stricttransportsecurity.preloadlist', False
        )
        # Enable detailed GeckoDriver logging
        firefox_options.set_capability(
            'moz:firefoxOptions', {'log': {'level': 'trace'}}
        )
        kwargs = dict(options=firefox_options)
        # Optional: Store logs in a file
        # Pass GECKO_LOG=1 when running tests
        GECKO_LOG = os.environ.get('GECKO_LOG', None)
        if GECKO_LOG:
            kwargs['service'] = webdriver.FirefoxService(log_output='geckodriver.log')
        cls.web_driver = webdriver.Firefox(**kwargs)

    @classmethod
    def tearDownClass(cls):
        cls.web_driver.quit()
        super().tearDownClass()

    def open(self, url, driver=None):
        """Opens a URL.

        Input Arguments:

        - url: URL to open
        - driver: selenium driver (default: cls.base_driver).
        """
        if not driver:
            driver = self.web_driver
        driver.get(f'{self.live_server_url}{url}')
        WebDriverWait(self.web_driver, 2).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '#main-content'))
        )

    def login(self, username=None, password=None, driver=None):
        """Log in to the admin dashboard.

        Input Arguments:

        - username: username to be used for login (default:
          cls.admin_username)
        - password: password to be used for login (default:
          cls.admin_password)
        - driver: selenium driver (default: cls.web_driver).
        """
        if not driver:
            driver = self.web_driver
        if not username:
            username = self.admin_username
        if not password:
            password = self.admin_password
        driver.get(f'{self.live_server_url}/admin/login/')
        if 'admin/login' in driver.current_url:
            driver.find_element(by=By.NAME, value='username').send_keys(username)
            driver.find_element(by=By.NAME, value='password').send_keys(password)
            driver.find_element(by=By.XPATH, value='//input[@type="submit"]').click()
