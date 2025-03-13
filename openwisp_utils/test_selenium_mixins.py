import os

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
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
        options = Options()
        options.page_load_strategy = 'eager'
        if os.environ.get('SELENIUM_HEADLESS', False):
            options.add_argument('--headless')
        GECKO_BIN = os.environ.get('GECKO_BIN', None)
        if GECKO_BIN:
            options.binary_location = GECKO_BIN
        options.set_preference('network.stricttransportsecurity.preloadlist', False)
        # Enable detailed GeckoDriver logging
        options.set_capability('moz:firefoxOptions', {'log': {'level': 'trace'}})
        # Use software rendering instead of hardware acceleration
        options.set_preference('gfx.webrender.force-disabled', True)
        options.set_preference('layers.acceleration.disabled', True)
        # Increase timeouts
        options.set_preference('marionette.defaultPrefs.update.disabled', True)
        options.set_preference('dom.max_script_run_time', 30)
        kwargs = dict(options=options)
        # Optional: Store logs in a file
        # Pass GECKO_LOG=1 when running tests
        GECKO_LOG = os.environ.get('GECKO_LOG', None)
        if GECKO_LOG:
            kwargs['service'] = webdriver.FirefoxService(log_output='geckodriver.log')
        cls.web_driver = webdriver.Firefox(**kwargs)
        # Firefox does not support the WebDriver.get_log API. To work around this,
        # we inject JavaScript into the page to override window.console within the
        # browser's JS runtime. This allows us to capture and retrieve console errors
        # directly from the page.
        extension_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "firefox-extensions",
                "console_capture_extension",
            )
        )
        cls.web_driver.install_addon(extension_path, temporary=True)

    @classmethod
    def tearDownClass(cls):
        cls.web_driver.quit()
        super().tearDownClass()

    def setUp(self):
        self.admin = self._create_admin(
            username=self.admin_username, password=self.admin_password
        )

    def open(self, url, driver=None, timeout=5):
        """Opens a URL.

        Input Arguments:

        - url: URL to open
        - driver: selenium driver (default: cls.base_driver).
        """
        if not driver:
            driver = self.web_driver
        driver.get(f'{self.live_server_url}{url}')
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        WebDriverWait(self.web_driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#main-content'))
        )

    def get_browser_logs(self):
        return self.web_driver.execute_script('return window._console_logs')

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

    def find_element(self, by, value, timeout=2, wait_for='visibility'):
        method = f'wait_for_{wait_for}'
        getattr(self, method)(by, value, timeout)
        return self.web_driver.find_element(by=by, value=value)

    def find_elements(self, by, value, timeout=2, wait_for='visibility'):
        method = f'wait_for_{wait_for}'
        getattr(self, method)(by, value, timeout)
        return self.web_driver.find_elements(by=by, value=value)

    def wait_for_visibility(self, by, value, timeout=2):
        return self.wait_for('visibility_of_element_located', by, value)

    def wait_for_invisibility(self, by, value, timeout=2):
        return self.wait_for('invisibility_of_element_located', by, value)

    def wait_for_presence(self, by, value, timeout=2):
        return self.wait_for('presence_of_element_located', by, value)

    def wait_for(self, method, by, value, timeout=2):
        try:
            return WebDriverWait(self.web_driver, timeout).until(
                getattr(EC, method)(((by, value)))
            )
        except TimeoutException as e:
            print(self.get_browser_logs())
            self.fail(f'{method} of "{value}" failed: {e}')
