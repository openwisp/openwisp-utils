import functools
import os
import threading
import time
from math import ceil
from uuid import uuid4

from django.conf import settings
from django.db.backends.base.base import BaseDatabaseWrapper
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.utils import free_port
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Maps the console method that produced a log entry to the level names also
# returned by Chrome's get_log("browser") API, so get_browser_logs() yields a
# consistent format across browsers.
FIREFOX_CONSOLE_LEVELS = {
    "log": "INFO",
    "info": "INFO",
    "debug": "DEBUG",
    "warn": "WARNING",
    "error": "SEVERE",
    "trace": "DEBUG",
    "assert": "SEVERE",
}


class SeleniumTestMixin:
    """A base Mixin Class for Selenium Browser Tests.

    Provides common initialization logic and helper methods.
    """

    admin_username = "admin"
    admin_password = "password"
    browser = "firefox"

    retry_max = 5
    retry_delay = 0
    retry_successes_required = 2
    retry_threshold = None
    ignored_browser_log_messages = (
        "BackupService.sys.mjs",
        "PrivateBrowsingUtils.sys.mjs",
        "PathUtils.join: PathUtils does not support empty paths",
    )
    _db_conn_lock = threading.RLock()
    _db_conn_serialized = False

    @classmethod
    def setUpClass(cls):
        # Apply before super().setUpClass() so the patch is active before the
        # live server (and any forked Daphne process) starts.
        cls._serialize_db_connection_lifecycle()
        super().setUpClass()
        cls.web_driver = cls.get_webdriver()

    @classmethod
    def tearDownClass(cls):
        cls.web_driver.quit()
        super().tearDownClass()

    @classmethod
    def _serialize_db_connection_lifecycle(cls):
        """Serialize SQLite connection open/close for the live-server tests.

        The selenium live-server test cases (WSGI
        ``StaticLiveServerTestCase`` and the Daphne/ASGI
        ``ChannelsLiveServerTestCase``) serve requests from several
        threads, so SQLite connections are opened and closed concurrently.
        On Python 3.13 this intermittently corrupts the C heap ("double
        free or corruption" / segmentation fault). Serializing connection
        open and close with a single process-wide lock removes the race.
        Together with the memoized ``find_library`` in
        ``openwisp_utils.db.backends.spatialite.base`` (which stops the
        per-connection ``ldconfig`` fork) this makes the live-server tests
        crash-free. No-op for non-SQLite backends.
        """
        if SeleniumTestMixin._db_conn_serialized:
            return
        engine = settings.DATABASES.get("default", {}).get("ENGINE", "")
        if "sqlite" not in engine and "spatialite" not in engine:
            return
        _orig_connect = BaseDatabaseWrapper.connect
        _orig_close = BaseDatabaseWrapper._close

        @functools.wraps(_orig_connect)
        def connect(self):
            with cls._db_conn_lock:
                return _orig_connect(self)

        @functools.wraps(_orig_close)
        def _close(self):
            with cls._db_conn_lock:
                return _orig_close(self)

        BaseDatabaseWrapper.connect = connect
        BaseDatabaseWrapper._close = _close
        SeleniumTestMixin._db_conn_serialized = True

    def _get_retry_successes_required(self):
        if self.retry_threshold is not None:
            return ceil(self.retry_max * self.retry_threshold)
        return self.retry_successes_required

    def _print_retry_message(self, test_name, attempt):
        print("-" * 80)
        print(f'[Retry] Retrying "{test_name}", attempt {attempt}/{self.retry_max}. ')
        print("-" * 80)

    def _setup_and_call(self, result, debug=False):
        """Override unittest.TestCase.run to retry flaky tests.

        This method is responsible for calling setUp and tearDown methods.
        Thus, we override this method to implement the retry mechanism
        instead of TestCase.run().
        """
        original_result = result
        test_name = self.id()
        success_count = 0
        failed_result = None
        retry_successes_required = self._get_retry_successes_required()
        # Manually call startTest to ensure TimeLoggingTestResult can
        # measure the execution time for the test.
        original_result.startTest(self)

        for attempt in range(self.retry_max + 1):
            # Use a new result object to prevent writing all attempts
            # to stdout.
            result = original_result.__class__(
                stream=None, descriptions=None, verbosity=0
            )
            super()._setup_and_call(result, debug)
            # IMPORTANT: a skip is not a success; propagate it as a skip and stop.
            if hasattr(result, "events"):
                skip_reasons = [
                    event[2] for event in result.events if event[0] == "addSkip"
                ]
            else:
                skip_reasons = [reason for _, reason in getattr(result, "skipped", [])]
            if skip_reasons:
                for reason in skip_reasons:
                    original_result.addSkip(self, reason)
                original_result.stopTest(self)
                return
            if result.wasSuccessful():
                if attempt == 0:
                    original_result.addSuccess(self)
                    return
                else:
                    success_count += 1
                    if success_count >= retry_successes_required:
                        original_result.addSuccess(self)
                        return
            else:
                failed_result = result
            if attempt < self.retry_max:
                self._print_retry_message(test_name, attempt + 1)
                if self.retry_delay:
                    time.sleep(self.retry_delay)

        if success_count < retry_successes_required:
            # If there are too few successful retries, copy the last failed
            # result to the original result.
            original_result.failures = failed_result.failures
            original_result.errors = failed_result.errors
            if hasattr(original_result, "events"):
                # Parallel tests uses RemoteTestResult which relies on events.
                original_result.events = failed_result.events
        else:
            # Mark the test as passed in the original result
            original_result.addSuccess(self)

    @classmethod
    def get_webdriver(cls):
        if cls.browser == "firefox":
            return cls.get_firefox_webdriver()
        return cls.get_chrome_webdriver()

    @classmethod
    def get_firefox_webdriver(cls):
        options = Options()
        options.page_load_strategy = "eager"
        if os.environ.get("SELENIUM_HEADLESS", False):
            options.add_argument("--headless")
        GECKO_BIN = os.environ.get("GECKO_BIN", None)
        if GECKO_BIN:
            options.binary_location = GECKO_BIN
        options.set_preference("network.stricttransportsecurity.preloadlist", False)
        # Enable detailed GeckoDriver logging
        options.set_capability("moz:firefoxOptions", {"log": {"level": "trace"}})
        # Use software rendering instead of hardware acceleration
        options.set_preference("gfx.webrender.force-disabled", True)
        options.set_preference("layers.acceleration.disabled", True)
        # Increase timeouts
        options.set_preference("marionette.defaultPrefs.update.disabled", True)
        options.set_preference("dom.max_script_run_time", 30)
        # Firefox does not support the WebDriver.get_log API, so console logs are
        # captured over WebDriver BiDi instead (see get_firefox_webdriver below).
        options.enable_bidi = True
        # When running Selenium tests with the "--parallel" flag,
        # each TestCase class requires its own browser instance.
        # If the same "remote-debugging-port" is used for all
        # TestCase classes, it leads to failed test cases.
        # Therefore, it is necessary to utilize different remote
        # debugging ports for each TestCase. To accomplish this,
        # we can leverage the randomized live test server port to
        # generate a unique port for each browser instance.
        options.set_capability(
            "moz:firefoxOptions", {"args": ["--marionette-port", free_port()]}
        )
        kwargs = dict(options=options)
        # Optional: Store logs in a file
        # Pass GECKO_LOG=1 when running tests
        GECKO_LOG = os.environ.get("GECKO_LOG", None)
        if GECKO_LOG:
            kwargs["service"] = webdriver.FirefoxService(log_output="geckodriver.log")
        web_driver = webdriver.Firefox(**kwargs)
        # Firefox does not support the WebDriver.get_log API. Capture console
        # messages over WebDriver BiDi, which records logs emitted during page
        # load (including errors) without relying on a browser extension. The
        # entries accumulate in driver._console_logs and are reset on every
        # top-level navigation to mirror the per-page semantics
        # get_browser_logs expects.
        web_driver._console_logs = []
        web_driver.script.add_console_message_handler(
            lambda entry: web_driver._console_logs.append(
                {
                    "level": FIREFOX_CONSOLE_LEVELS.get(entry.method, "INFO"),
                    "message": entry.text,
                }
            )
        )
        # Reset the buffer only when the top-level context under test navigates.
        # The id of that context stays stable across navigations, while iframes
        # and other secondary contexts have different ids; clearing on their
        # navigations would wipe the page's logs before get_browser_logs() reads
        # them. Subscribing with contexts=[id] still delivers child-context
        # events, so the context is filtered here in the callback instead.
        top_level_context = web_driver.current_window_handle

        def reset_logs_on_top_level_navigation(info):
            if info.context == top_level_context:
                web_driver._console_logs.clear()

        web_driver.browsing_context.add_event_handler(
            "navigation_started", reset_logs_on_top_level_navigation
        )
        return web_driver

    @classmethod
    def get_chrome_webdriver(cls):
        options = webdriver.ChromeOptions()
        options.page_load_strategy = "eager"
        if os.environ.get("SELENIUM_HEADLESS", False):
            options.add_argument("--headless")
        CHROME_BIN = os.environ.get("CHROME_BIN", None)
        if CHROME_BIN:
            options.binary_location = CHROME_BIN
        options.add_argument("--window-size=1366,768")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-features=VizDisplayCompositor")
        # When running Selenium tests with the "--parallel" flag,
        # each TestCase class requires its own browser instance.
        # If the same "remote-debugging-port" is used for all
        # TestCase classes, it leads to failed test cases.
        # Therefore, it is necessary to utilize different remote
        # debugging ports for each TestCase. To accomplish this,
        # we can leverage the randomized live test server port to
        # generate a unique port for each browser instance.
        options.add_argument(f"--remote-debugging-port={free_port()}")
        options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
        return webdriver.Chrome(
            options=options,
        )

    def setUp(self):
        self.admin = self._create_admin(
            username=self.admin_username, password=self.admin_password
        )

    def open(self, url, html_container="#main-content", driver=None, timeout=5):
        """Opens a URL.

        Input Arguments:

        - url: URL to open
        - driver: selenium driver (default: cls.base_driver).
        - html_container: CSS selector of an HTML element to look for once
          the page is ready
        - timeout: timeout until the page is ready
        """
        driver = driver or self.web_driver
        driver.get(f"{self.live_server_url}{url}")
        self._wait_until_page_ready(driver=driver, html_container=html_container)

    def _wait_until_page_ready(
        self, html_container="#main-content", timeout=5, driver=None
    ):
        driver = driver or self.web_driver
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        self.wait_for_visibility(By.CSS_SELECTOR, html_container, timeout, driver)

    def get_browser_logs(self, driver=None):
        driver = driver or self.web_driver
        if self.browser == "firefox":
            self._flush_firefox_console_logs(driver)
            return list(driver._console_logs)
        return driver.get_log("browser")

    def get_browser_errors(self, driver=None):
        return [
            log
            for log in self.get_browser_logs(driver=driver)
            if log.get("level") == "SEVERE"
            if not any(
                ignored_message in log.get("message", "")
                for ignored_message in self.ignored_browser_log_messages
            )
        ]

    def _flush_firefox_console_logs(self, driver, timeout=2):
        """Wait for pending BiDi console messages to be delivered.

        BiDi console events arrive asynchronously, so a log emitted right
        before get_browser_logs() may not have been recorded yet. Emit a
        sentinel message and wait until it is seen: because console events
        are delivered in order, all earlier messages have arrived by then.
        The sentinel is removed before returning.
        """
        sentinel = f"__owisp_console_flush_{uuid4().hex}__"
        driver.execute_script("console.debug(arguments[0]);", sentinel)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if any(sentinel in entry["message"] for entry in driver._console_logs):
                break
            time.sleep(0.02)
        driver._console_logs[:] = [
            entry for entry in driver._console_logs if sentinel not in entry["message"]
        ]

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
        driver.get(f"{self.live_server_url}/admin/login/")
        self._wait_until_page_ready(driver=driver)
        if "admin/login" in driver.current_url:
            self.find_element(by=By.NAME, value="username", driver=driver).send_keys(
                username
            )
            self.find_element(by=By.NAME, value="password", driver=driver).send_keys(
                password
            )
            self.find_element(
                by=By.XPATH, value='//input[@type="submit"]', driver=driver
            ).click()
        self._wait_until_page_ready(driver=driver)

    def logout(self, driver=None):
        driver = driver or self.web_driver
        self.find_element(By.CSS_SELECTOR, ".account-button", driver=driver).click()
        self.find_element(By.CSS_SELECTOR, "#logout-form button", driver=driver).click()

    def find_element(self, by, value, timeout=2, driver=None, wait_for="visibility"):
        driver = driver or self.web_driver
        method = f"wait_for_{wait_for}"
        getattr(self, method)(by, value, timeout, driver=driver)
        return driver.find_element(by=by, value=value)

    def find_elements(self, by, value, timeout=2, driver=None, wait_for="visibility"):
        driver = driver or self.web_driver
        method = f"wait_for_{wait_for}"
        getattr(self, method)(by, value, timeout, driver=driver)
        return driver.find_elements(by=by, value=value)

    def wait_for_visibility(self, by, value, timeout=2, driver=None):
        driver = driver or self.web_driver
        return self.wait_for(
            "visibility_of_element_located", by, value, timeout, driver
        )

    def wait_for_invisibility(self, by, value, timeout=2, driver=None):
        driver = driver or self.web_driver
        return self.wait_for(
            "invisibility_of_element_located", by, value, timeout, driver
        )

    def wait_for_presence(self, by, value, timeout=2, driver=None):
        driver = driver or self.web_driver
        return self.wait_for("presence_of_element_located", by, value, timeout, driver)

    def wait_for(self, method, by, value, timeout=2, driver=None):
        driver = driver or self.web_driver
        try:
            return WebDriverWait(driver, timeout).until(
                getattr(EC, method)((by, value))
            )
        except TimeoutException as e:
            print(self.get_browser_logs(driver))
            self.fail(f'{method} of "{value}" failed: {e}')

    def hide_loading_overlay(self, html_id="loading-overlay", timeout=2, driver=None):
        """The geckodriver can't figure out the loading overlay is still fading out, so let's just hide it."""
        driver = driver or self.web_driver
        element_exists = driver.execute_script(
            f'var el = document.getElementById("{html_id}"); '
            f'if (el) {{ el.style.display="none"; return true; }} return false;'
        )
        # Only wait if element exists
        if element_exists:
            self.wait_for_invisibility(By.ID, html_id, timeout, driver)
