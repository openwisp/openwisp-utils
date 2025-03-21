import os

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.utils import free_port
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class SeleniumTestMixin:
    """A base Mixin Class for Selenium Browser Tests.

    Provides common initialization logic and helper methods.
    """

    admin_username = 'admin'
    admin_password = 'password'
    browser = 'firefox'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if cls.browser == 'firefox':
            cls.web_driver = cls.get_firefox_webdriver()
        else:
            cls.web_driver = cls.get_chrome_webdriver()

    @classmethod
    def get_firefox_webdriver(cls):
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
        # When running Selenium tests with the "--parallel" flag,
        # each TestCase class requires its own browser instance.
        # If the same "remote-debugging-port" is used for all
        # TestCase classes, it leads to failed test cases.
        # Therefore, it is necessary to utilize different remote
        # debugging ports for each TestCase. To accomplish this,
        # we can leverage the randomized live test server port to
        # generate a unique port for each browser instance.
        options.set_capability(
            'moz:firefoxOptions', {'args': ['--marionette-port', free_port()]}
        )
        kwargs = dict(options=options)
        # Optional: Store logs in a file
        # Pass GECKO_LOG=1 when running tests
        GECKO_LOG = os.environ.get('GECKO_LOG', None)
        if GECKO_LOG:
            kwargs['service'] = webdriver.FirefoxService(log_output='geckodriver.log')
        web_driver = webdriver.Firefox(**kwargs)
        # Firefox does not support the WebDriver.get_log API. To work around this,
        # we inject JavaScript into the page to override window.console within the
        # browser's JS runtime. This allows us to capture and retrieve console errors
        # directly from the page.
        extension_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                'firefox-extensions',
                'console_capture_extension',
            )
        )
        web_driver.install_addon(extension_path, temporary=True)
        return web_driver

    @classmethod
    def get_chrome_webdriver(cls):
        options = webdriver.ChromeOptions()
        options.page_load_strategy = 'eager'
        if os.environ.get('SELENIUM_HEADLESS', False):
            options.add_argument('--headless')
        CHROME_BIN = os.environ.get('CHROME_BIN', None)
        if CHROME_BIN:
            options.binary_location = CHROME_BIN
        options.add_argument('--window-size=1366,768')
        options.add_argument('--ignore-certificate-errors')
        # When running Selenium tests with the "--parallel" flag,
        # each TestCase class requires its own browser instance.
        # If the same "remote-debugging-port" is used for all
        # TestCase classes, it leads to failed test cases.
        # Therefore, it is necessary to utilize different remote
        # debugging ports for each TestCase. To accomplish this,
        # we can leverage the randomized live test server port to
        # generate a unique port for each browser instance.
        options.add_argument(f'--remote-debugging-port={free_port()}')
        options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
        return webdriver.Chrome(
            options=options,
        )

    @classmethod
    def tearDownClass(cls):
        cls.web_driver.quit()
        super().tearDownClass()

    def setUp(self):
        self.admin = self._create_admin(
            username=self.admin_username, password=self.admin_password
        )

    def open(self, url, html_container='#main-content', driver=None, timeout=5):
        """Opens a URL.

        Input Arguments:

        - url: URL to open
        - driver: selenium driver (default: cls.base_driver).
        - html_container: CSS selector of an HTML element to look for once
          the page is ready
        - timeout: timeout until the page is ready
        """
        driver = driver or self.web_driver
        driver.get(f'{self.live_server_url}{url}')
        self._wait_until_page_ready(driver=driver, html_container=html_container)

    def _wait_until_page_ready(
        self, html_container='#main-content', timeout=5, driver=None
    ):
        driver = driver or self.web_driver
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        self.wait_for_visibility(By.CSS_SELECTOR, html_container, timeout, driver)

    def get_browser_logs(self, driver=None):
        driver = driver or self.web_driver
        if self.browser == 'firefox':
            return driver.execute_script('return window._console_logs')
        return driver.get_log('browser')

    def login(self, username=None, password=None, driver=None):
        """Log in to the admin dashboard.

        Input Arguments:

        - username: username to be used for login (default:
          cls.admin_username)
        - password: password to be used for login (default:
          cls.admin_password)
        - driver: selenium driver (default: cls.web_driver).
        """
        driver = driver or self.web_driver
        if not username:
            username = self.admin_username
        if not password:
            password = self.admin_password
        driver.get(f'{self.live_server_url}/admin/login/')
        self._wait_until_page_ready(driver=driver)
        if 'admin/login' in driver.current_url:
            driver.find_element(by=By.NAME, value='username').send_keys(username)
            driver.find_element(by=By.NAME, value='password').send_keys(password)
            driver.find_element(by=By.XPATH, value='//input[@type="submit"]').click()
        self._wait_until_page_ready(driver=driver)

    def find_element(self, by, value, timeout=2, driver=None, wait_for='visibility'):
        driver = driver or self.web_driver
        method = f'wait_for_{wait_for}'
        getattr(self, method)(by, value, timeout)
        return driver.find_element(by=by, value=value)

    def find_elements(self, by, value, timeout=2, driver=None, wait_for='visibility'):
        driver = driver or self.web_driver
        method = f'wait_for_{wait_for}'
        getattr(self, method)(by, value, timeout)
        return driver.find_elements(by=by, value=value)

    def wait_for_visibility(self, by, value, timeout=2, driver=None):
        driver = driver or self.web_driver
        return self.wait_for(
            'visibility_of_element_located', by, value, timeout, driver
        )

    def wait_for_invisibility(self, by, value, timeout=2, driver=None):
        driver = driver or self.web_driver
        return self.wait_for(
            'invisibility_of_element_located', by, value, timeout, driver
        )

    def wait_for_presence(self, by, value, timeout=2, driver=None):
        driver = driver or self.web_driver
        return self.wait_for('presence_of_element_located', by, value, timeout, driver)

    def wait_for(self, method, by, value, timeout=2, driver=None):
        driver = driver or self.web_driver
        try:
            return WebDriverWait(driver, timeout).until(
                getattr(EC, method)(((by, value)))
            )
        except TimeoutException as e:
            print(self.get_browser_logs(driver))
            self.fail(f'{method} of "{value}" failed: {e}')

    def hide_loading_overlay(self, html_id='loading-overlay', timeout=2, driver=None):
        """The geckodriver can't figure out the loading overlay is still fading out, so let's just hide it."""
        driver = driver or self.web_driver
        driver.execute_script(
            f'document.getElementById("{html_id}").style.display="none";'
        )
        self.wait_for_invisibility(By.ID, html_id, timeout, driver)
