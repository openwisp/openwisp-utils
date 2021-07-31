from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .utils import SeleniumTestCase


class TestMenu(SeleniumTestCase):
    admin_username = 'admin'
    admin_password = 'password'
    maxamize_menu = 'Maximize menu'
    minimize_menu = 'Minimize menu'
    transition = 'none 0s ease 0s'
    # none because transition has been set to none during tests

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--window-size=1366,768')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--remote-debugging-port=9222')
        capabilities = DesiredCapabilities.CHROME
        capabilities['goog:loggingPrefs'] = {'browser': 'ALL'}
        cls.web_driver = webdriver.Chrome(
            options=chrome_options, desired_capabilities=capabilities
        )

    @classmethod
    def tearDownClass(cls):
        cls.web_driver.quit()
        super().tearDownClass()

    def tearDown(self):
        # Clear local storage
        self.web_driver.execute_script('window.localStorage.clear()')

    def setUp(self):
        self.admin = self._create_admin(
            username=self.admin_username, password=self.admin_password
        )

    def test_addition_of_transition_effect(self):
        self.login()
        menu = self.web_driver.find_element_by_id('menu')
        main_content = self._get_main_content()
        menu_toggle = self._get_menu_toggle()
        self.assertEqual(menu.value_of_css_property('transition'), self.transition)
        self.assertEqual(
            main_content.value_of_css_property('transition'), self.transition
        )
        self.assertEqual(
            menu_toggle.value_of_css_property('transition'), self.transition
        )

    def _test_menu_state(self, open, is_narrow=False):
        logo = self._get_logo()
        hamburger = self._get_hamburger()
        menu_item_label = self._get_menu_home_item_label()
        menu_toggle = self._get_menu_toggle()
        container = self._get_container()
        nav = self._get_nav()
        if open:
            self.assertEqual(logo.is_displayed(), True)
            self.assertEqual(nav.is_displayed(), True)
            if is_narrow:
                self.assertEqual(hamburger.is_displayed(), True)
                self.assertEqual(menu_toggle.is_displayed(), False)
            else:
                self.assertEqual(hamburger.is_displayed(), False)
                self.assertEqual(menu_toggle.is_displayed(), True)
            self.assertEqual(menu_item_label.is_displayed(), True)
            self.assertEqual(menu_toggle.get_attribute('title'), self.minimize_menu)
            self.assertEqual(container.get_attribute('class'), '')
        else:
            if is_narrow:
                self.assertEqual(nav.is_displayed(), False)
                self.assertEqual(logo.is_displayed(), True)
                self.assertEqual(menu_toggle.is_displayed(), False)
            else:
                self.assertEqual(nav.is_displayed(), True)
                self.assertEqual(logo.is_displayed(), False)
                self.assertEqual(menu_item_label.is_displayed(), False)
                self.assertEqual(menu_toggle.is_displayed(), True)
            self.assertEqual(hamburger.is_displayed(), True)
            self.assertEqual(menu_toggle.get_attribute('title'), self.maxamize_menu)
            container_class = container.get_attribute('class')
            self.assertEqual(container_class, 'toggle-menu')

    def test_menu_on_wide_screen(self):
        self.login()
        with self.subTest('Test menu is open on first load'):
            self._test_menu_state(True)
        with self.subTest('Test menu remains open on page change or refresh'):
            self.web_driver.refresh()
            WebDriverWait(self.web_driver, 2).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="site-name"]'))
            )
            self._test_menu_state(True)
        menu_toggle = self._get_menu_toggle()
        with self.subTest('Test menu gets closed on clicking menu-toggle'):
            menu_toggle.click()
            self._test_menu_state(False)

        with self.subTest('Test menu menu remains close on page change or refresh'):
            self.web_driver.refresh()
            WebDriverWait(self.web_driver, 2).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@class="hamburger"]'))
            )
            self._test_menu_state(False)
        menu_toggle = self._get_menu_toggle()
        with self.subTest('Test menu gets open on clicking menu-toggle'):
            menu_toggle.click()
            self._test_menu_state(True)
        hamburger = self._get_hamburger()
        self._close_menu()
        with self.subTest('Test menu gets open on clicking hamburger'):
            hamburger.click()
            self._test_menu_state(True)
        self._test_account_component()
        self._test_menu_dropdown()
        with self.subTest('Test menu on popup page'):
            self._test_popup_page()
        self._test_login_and_logout_page()

    def test_menu_on_medium_screen(self):
        self.login()
        self.web_driver.set_window_size(980, 600)
        menu_toggle = self._get_menu_toggle()
        menu_backdrop = self._get_menu_backdrop()
        with self.subTest('Test menu remains close on first load'):
            self._test_menu_state(False)
            self.assertEqual(menu_backdrop.is_displayed(), False)
        with self.subTest('Test menu gets open on clicking menu_toggle'):
            menu_toggle.click()
            self._test_menu_state(True)
            self.assertEqual(menu_backdrop.is_displayed(), True)

        with self.subTest('Test menu gets closed on clicking menu_backdrop'):
            menu_backdrop.click()
            self._test_menu_state(False)
            self.assertEqual(menu_backdrop.is_displayed(), False)
        self._open_menu()
        self.web_driver.refresh()
        WebDriverWait(self.web_driver, 2).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@class="hamburger"]'))
        )
        with self.subTest('Test menu remains close on page change or refresh'):
            self._test_menu_state(False)
        self._test_account_component()
        self._test_menu_dropdown(is_medium=True)
        with self.subTest('Test menu on popup page'):
            self._test_popup_page()
        self._test_login_and_logout_page()
        self.web_driver.set_window_size(1366, 768)

    def test_menu_on_narrow_screen(self):
        self.login()
        self.web_driver.set_window_size(450, 600)
        hamburger = self._get_hamburger()
        menu_backdrop = self._get_menu_backdrop()
        with self.subTest('Test menu remains close on first load'):
            self._test_menu_state(False, is_narrow=True)
            self.assertEqual(menu_backdrop.is_displayed(), False)
        with self.subTest('Test opening of menu'):
            hamburger.click()
            self._test_menu_state(True, is_narrow=True)
            self.assertEqual(menu_backdrop.is_displayed(), False)
        self.web_driver.refresh()
        with self.subTest('Test menu do not remain open on page change or refresh'):
            self._test_menu_state(False, is_narrow=True)
        self._test_account_component(is_narrow=True)
        self._test_menu_dropdown(is_narrow=True)
        with self.subTest('Test menu on popup page'):
            self._test_popup_page()
        self._test_login_and_logout_page()
        self.web_driver.set_window_size(1366, 768)

    def _test_login_and_logout_page(self, is_logged_in=True):
        if not is_logged_in:
            self.login()
        self.logout()
        # Test logout page
        hamburger = self._get_hamburger()
        logo = self._get_logo()
        self.assertEqual(hamburger.is_displayed(), False)
        self.assertEqual(logo.is_displayed(), True)
        with self.assertRaises(NoSuchElementException):
            self._get_menu_toggle()
            self._get_nav()
        main_content = self._get_main_content()
        self.assertEqual(main_content.get_attribute('class'), 'm-0')
        # Test login page
        self.web_driver.refresh()
        WebDriverWait(self.web_driver, 2).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="site-name"]'))
        )
        hamburger = self._get_hamburger()
        logo = self._get_logo()
        main_content = self._get_main_content()
        self.assertEqual(hamburger.is_displayed(), False)
        self.assertEqual(logo.is_displayed(), True)
        with self.assertRaises(NoSuchElementException):
            self._get_menu_toggle()
        with self.assertRaises(NoSuchElementException):
            self._get_nav()
        main_content = self._get_main_content()
        self.assertEqual(main_content.get_attribute('class'), 'm-0')

    def _test_account_component(self, is_logged_in=True, is_narrow=False):
        if not is_logged_in:
            self.login()
        '''
        should_be_visible:
            should account_button username be visible on the screen.
            if medium and wide: True
            else: False
        '''
        should_be_visible = not is_narrow
        if is_narrow:
            menu_toggle = self._get_hamburger()
        else:
            menu_toggle = self._get_menu_toggle()
        account_button = self._get_account_button()
        account_dropdown = self._get_account_dropdown()
        account_button_username = self._get_account_button_username()
        account_dropdown_username = self._get_account_dropdown_username()
        with self.subTest('Test account button and username visiblility'):
            # When menu is open
            self._open_menu()
            self.assertEqual(account_button.is_displayed(), True)
            self.assertEqual(account_button_username.is_displayed(), should_be_visible)
            # When menu is close
            menu_toggle.click()
            self.assertEqual(account_button.is_displayed(), True)
            self.assertEqual(account_button_username.is_displayed(), should_be_visible)

        with self.subTest('Test account dropdown visibility'):
            self.assertEqual(account_dropdown.is_displayed(), False)
            account_button.click()
            self.assertEqual(account_dropdown.is_displayed(), True)
            if should_be_visible:
                self.assertEqual(account_dropdown_username.is_displayed(), False)
            else:
                self.assertEqual(account_dropdown_username.is_displayed(), True)
            account_button.click()
            self.assertEqual(account_dropdown.is_displayed(), False)

    def _test_menu_dropdown(self, is_narrow=False, is_medium=False):
        self._open_menu()
        mg_head = self._get_test_mg_head()
        mg_label = self._get_test_mg_label()
        mg_dropdown = self._get_test_mg_dropdown()
        mg_icon = self._get_test_mg_icon()
        main_content = self._get_main_content()
        mg_dropdown_label = self._get_test_mg_dropdown_label()
        with self.subTest('Test menu dropdown when menu is open'):
            # When menu group is not visible
            self.assertEqual(mg_dropdown.is_displayed(), False)
            self.assertEqual(mg_label.is_displayed(), True)
            # Test mg dropdown gets visible on clicking mg head
            mg_head.click()
            self.assertEqual(mg_dropdown.is_displayed(), True)
            self.assertEqual(mg_dropdown_label.is_displayed(), False)
            # Test mg dropdown gets invisible on clicking mg head again
            mg_head.click()
            self.assertEqual(mg_dropdown.is_displayed(), False)
            # Test menu dropdown gets invisible when clicked outside on wide screen
            if not is_medium and not is_narrow:
                mg_head.click()  # Show dropdown
                main_content.click()
                self.assertEqual(mg_dropdown.is_displayed(), False)

        if is_narrow:
            # Do not test when menu is not visible
            return
        with self.subTest('Test menu dropdown when menu is close'):
            self._close_menu()
            # Test mg_dropdown is not visible
            self.assertEqual(mg_dropdown.is_displayed(), False)
            self.assertEqual(mg_label.is_displayed(), False)
            self.assertEqual(mg_icon.is_displayed(), True)
            # Test mg dropdown gets visible on clicking mg head
            mg_head.click()
            self.assertEqual(mg_dropdown.is_displayed(), True)
            self.assertEqual(mg_dropdown_label.is_displayed(), True)
            # Test mg dropdown gets invisible on clicking mg head
            mg_head.click()
            self.assertEqual(mg_dropdown.is_displayed(), False)
            # Test menu dropdown gets invisible when clicked outside
            mg_head.click()  # Show dropdown
            main_content.click()
            self.assertEqual(mg_dropdown.is_displayed(), False)

        with self.subTest('Test visibilty of menu label when menu close'):
            self._close_menu()
            actions = ActionChains(self.web_driver)
            actions.move_to_element(mg_head)
            actions.perform()
            self.assertEqual(mg_label.is_displayed(), True)
            mg_head.click()
            actions.move_to_element(mg_head)
            actions.perform()
            self.assertEqual(mg_label.is_displayed(), False)

    def _test_popup_page(self):
        self.open('/admin/auth/user/add/?_to_field=id&_popup=1')
        WebDriverWait(self.web_driver, 2).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="main-content"]'))
        )
        with self.assertRaises(NoSuchElementException):
            self._get_menu()
        self.open('/admin/')
        WebDriverWait(self.web_driver, 2).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="main-content"]'))
        )
