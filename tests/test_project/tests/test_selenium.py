from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..models import Book, Operator, Shelf
from . import CreateMixin
from .utils import SeleniumTestMixin


class TestMenu(SeleniumTestMixin, StaticLiveServerTestCase):
    def setUp(self):
        self.admin = self._create_admin()

    def tearDown(self):
        # Clear local storage
        self.web_driver.execute_script('window.localStorage.clear()')

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
            self.assertEqual(
                menu_toggle.get_attribute('title'), self.config['minimize_menu']
            )
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
            self.assertEqual(
                menu_toggle.get_attribute('title'), self.config['maximize_menu']
            )
            container_class = container.get_attribute('class')
            self.assertIn(
                'toggle-menu',
                container_class,
            )

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
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, self.config['site_name_css_selector'])
            )
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
        # should_be_visible:
        #     should account_button username be visible on the screen.
        #     if medium and wide: True
        #     else: False
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
            is_visible = True
            try:
                WebDriverWait(self.web_driver, 2).until(
                    EC.visibility_of_element_located(
                        (By.CSS_SELECTOR, '#mg-dropdown-32')
                    )
                )
            except TimeoutException:
                is_visible = False
            self.assertEqual(
                is_visible,
                True,
            )
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
            is_visible = True
            try:
                WebDriverWait(self.web_driver, 2).until(
                    EC.visibility_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            '#mg-control-32 > div:nth-child(1) > span:nth-child(2)',
                        )
                    )
                )
            except TimeoutException:
                is_visible = False
            self.assertEqual(is_visible, True)
            mg_head.click()
            actions.move_to_element(mg_head)
            actions.perform()
            self.assertEqual(mg_label.is_displayed(), False)

    def _test_popup_page(self):
        url = reverse('admin:auth_user_add') + '?_to_field=id&_popup=1'
        self.open(url)
        with self.assertRaises(NoSuchElementException):
            self._get_menu()
        self.open(reverse('admin:index'))

    def test_addition_of_transition_effect(self):
        transition = 'none 0s ease 0s'
        # none because transition has been set to none during tests
        self.login()
        menu = self.web_driver.find_element(By.ID, 'menu')
        main_content = self._get_main_content()
        menu_toggle = self._get_menu_toggle()
        self.assertEqual(menu.value_of_css_property('transition'), transition)
        self.assertEqual(main_content.value_of_css_property('transition'), transition)
        self.assertEqual(menu_toggle.value_of_css_property('transition'), transition)

    def test_menu_on_wide_screen(self):
        self.login()
        with self.subTest('Test menu is open on first load'):
            self._test_menu_state(True)
        with self.subTest('Test menu remains open on page change or refresh'):
            self.web_driver.refresh()
            WebDriverWait(self.web_driver, 2).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, self.config['site_name_css_selector'])
                )
            )
            self._test_menu_state(True)
        menu_toggle = self._get_menu_toggle()
        with self.subTest('Test menu gets closed on clicking menu-toggle'):
            menu_toggle.click()
            self._test_menu_state(False)

        with self.subTest('Test menu menu remains close on page change or refresh'):
            self.web_driver.refresh()
            WebDriverWait(self.web_driver, 2).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, self.config['hamburger_css_selector'])
                )
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
        self._open_menu()
        with self.subTest('Test menu on popup page'):
            self._test_popup_page()
        self._test_login_and_logout_page()

    def test_active_menu_group(self):
        """
        Test active menu group:
        - Active group should close only when clicked on menu else
          it should remain open.
        """
        self.login()
        url = reverse('admin:auth_user_changelist')
        self.open(url)
        WebDriverWait(self.web_driver, 2).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, self.config['site_name_css_selector'])
            )
        )
        with self.subTest('Test active menu group on wide screen'):
            active_mg = self._get_active_mg()
            account_button = self._get_account_button()
            toggle_button = self._get_menu_toggle()
            self.assertEqual(active_mg.is_displayed(), True)
            account_button.click()
            self.assertEqual(active_mg.is_displayed(), True)
            toggle_button.click()
            self.assertEqual(active_mg.is_displayed(), False)
            toggle_button.click()
            self.assertEqual(active_mg.is_displayed(), True)
            # now close the group
            mg_head = self._get_active_mg_head()
            mg_head.click()
            self.assertEqual(active_mg.is_displayed(), False)
            toggle_button.click()
            self.assertEqual(active_mg.is_displayed(), False)
            toggle_button.click()
            self.assertEqual(active_mg.is_displayed(), False)

        with self.subTest('Test active menu group on medium screen'):
            self.web_driver.set_window_size(980, 600)
            self.web_driver.refresh()
            WebDriverWait(self.web_driver, 2).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, self.config['hamburger_css_selector'])
                )
            )
            active_mg = self._get_active_mg()
            toggle_button = self._get_menu_toggle()
            self.assertEqual(active_mg.is_displayed(), False)
            toggle_button.click()
            self.assertEqual(active_mg.is_displayed(), True)
            mg_head = self._get_active_mg_head()
            mg_head.click()
            toggle_button.click()
            toggle_button.click()
            self.assertEqual(active_mg.is_displayed(), False)

        with self.subTest('Test active menu group on narrow screen'):
            self.web_driver.set_window_size(450, 600)
            self.web_driver.refresh()
            active_mg = self._get_active_mg()
            hamburger = self._get_hamburger()
            account_button = self._get_account_button()
            WebDriverWait(self.web_driver, 2).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, self.config['hamburger_css_selector'])
                )
            )
            hamburger.click()
            self.assertEqual(active_mg.is_displayed(), True)
            account_button.click()
            self.assertEqual(active_mg.is_displayed(), True)
            mg_head = self._get_active_mg_head()
            mg_head.click()
            hamburger.click()
            hamburger.click()
            self.assertEqual(active_mg.is_displayed(), False)
        self.web_driver.set_window_size(1366, 768)

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
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, self.config['hamburger_css_selector'])
            )
        )
        with self.subTest('Test menu remains close on page change or refresh'):
            self._test_menu_state(False)
        self._test_account_component()
        self._test_menu_dropdown(is_medium=True)
        with self.subTest('Test menu on popup page'):
            self._test_popup_page()
        # Test active menu group
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


class TestBasicFilter(SeleniumTestMixin, StaticLiveServerTestCase, CreateMixin):
    shelf_model = Shelf
    book_model = Book

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.admin = self._create_admin()
        self.web_driver.set_window_size(1600, 768)
        self._create_test_data()

    def _create_test_data(self):
        # create two users
        tester1 = self._create_admin(username='tester1')
        self._create_admin(username='tester2')
        # creating 2 Horror and 2 Fantasy shelfs.
        # tester1 is the owner of all books
        for i in range(2):
            horror_shelf = self._create_shelf(
                name='horror' + str(i), books_type='HORROR', owner=tester1
            )
        for i in range(2):
            fantasy_shelf = self._create_shelf(
                name='fantasy' + str(i), books_type='FANTASY', owner=tester1
            )
        self._create_book(name='horror book', shelf=horror_shelf)
        self._create_book(name='fantasy book', shelf=fantasy_shelf)

    def test_shelf_filter(self):
        # It has total number of filters greater than 4
        self.login()
        url = reverse('admin:test_project_shelf_changelist')
        self.open(url)
        dropdown = self._get_filter_dropdown('type-of-book')
        title = self._get_filter_title('type-of-book')
        main_content = self._get_main_content()
        selected_option = self._get_filter_selected_option('type-of-book')
        with self.subTest('Test visibility of filter'):
            self.assertEqual(self.check_exists_by_id('ow-changelist-filter'), True)

        with self.subTest('Test visibility of filter button'):
            self.assertEqual(self.check_exists_by_id('ow-apply-filter'), True)

        with self.subTest('Test filter dropdown is not visible'):
            self.assertEqual(dropdown.is_displayed(), False)

        with self.subTest('Test anchor tag in filter options'):
            self.assertEqual(
                self.check_exists_by_css_selector('.type-of-book .filter-options a'),
                True,
            )

        with self.subTest('Test filter dropdown is visbility'):
            title.click()
            self.wait_for_dropdown('type-of-book')
            self.assertEqual(dropdown.is_displayed(), True)
            title.click()
            self.assertEqual(dropdown.is_displayed(), False)
            title.click()
            self.wait_for_dropdown('type-of-book')
            self.assertEqual(dropdown.is_displayed(), True)
            main_content.click()
            self.assertEqual(dropdown.is_displayed(), False)

        with self.subTest('Test changing of filter option'):
            title.click()  # Open dropdown
            self.wait_for_dropdown('type-of-book')
            old_value = selected_option.get_attribute('innerText')
            fantasy_option = self._get_filter_anchor('books_type__exact=FANTASY')
            fantasy_option.click()
            self.assertEqual(dropdown.is_displayed(), False)
            self.assertNotEqual(selected_option.get_attribute('innerText'), old_value)
            self.assertEqual(selected_option.get_attribute('innerText'), 'FANTASY')

        filter_button = self._get_filter_button()
        with self.subTest('Test apply filter'):
            filter_button.click()
            WebDriverWait(self.web_driver, 2).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '#site-name'))
            )
            self.assertEqual(self.check_exists_by_id('changelist-filter-clear'), True)
            paginator = self.web_driver.find_element(By.CSS_SELECTOR, '.paginator')
            self.assertEqual(paginator.get_attribute('innerText'), '2 shelfs')

        with self.subTest('Test clear filter button'):
            clear_button = self._get_clear_button()
            clear_button.click()
            WebDriverWait(self.web_driver, 2).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '#site-name'))
            )
            paginator = self.web_driver.find_element(By.CSS_SELECTOR, '.paginator')
            self.assertEqual(paginator.get_attribute('innerText'), '4 shelfs')

        with self.subTest('Test multiple filters'):
            # Select Fantasy book type
            books_type_title = self._get_filter_title('type-of-book')
            owner_filter_xpath = '//*[@id="select2-id-owner_id-dal-filter-container"]'
            owner_filter_option_xpath = (
                '//*[@id="select2-id-owner_id-dal-filter-results"]/li[4]'
            )
            owner_filter = self.web_driver.find_element(By.XPATH, owner_filter_xpath)
            books_type_title.click()
            fantasy_option = self._get_filter_anchor('books_type__exact=FANTASY')
            fantasy_option.click()
            owner_filter.click()
            WebDriverWait(self.web_driver, 2).until(
                EC.visibility_of_element_located((By.XPATH, owner_filter_option_xpath))
            )
            owner_option = self.web_driver.find_element(
                By.XPATH, owner_filter_option_xpath
            )
            owner_option.click()
            filter_button = self._get_filter_button()
            filter_button.click()
            WebDriverWait(self.web_driver, 2).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '#site-name'))
            )
            paginator = self.web_driver.find_element(By.CSS_SELECTOR, '.paginator')
            self.assertEqual(paginator.get_attribute('innerText'), '0 shelfs')

    def test_book_filter(self):
        # It has total number of filters less than 4
        self.login()
        url = reverse('admin:test_project_book_changelist')
        self.open(url)
        with self.subTest('Test visibility of filter'):
            self.assertEqual(self.check_exists_by_id('ow-changelist-filter'), True)

        with self.subTest('Test filter button is not visible'):
            self.assertEqual(self.check_exists_by_id('ow-apply-filter'), False)

        with self.subTest('Test anchor tag in filter options'):
            self.assertEqual(
                self.check_exists_by_css_selector('.name .filter-options a'), True
            )

        with self.subTest('Test dropdown and apply filter'):
            dropdown = self._get_filter_dropdown('name')
            title = self._get_filter_title('name')
            option = self._get_filter_anchor('name=horror+book')
            selected_option = self._get_filter_selected_option('name')
            old_value = selected_option.get_attribute('innerText')
            self.assertEqual(dropdown.is_displayed(), False)
            title.click()
            self.wait_for_dropdown('name')
            self.assertEqual(dropdown.is_displayed(), True)
            option.click()
            WebDriverWait(self.web_driver, 2).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '#site-name'))
            )
            selected_option = self._get_filter_selected_option('name')
            self.assertNotEqual(old_value, selected_option.get_attribute('innerText'))
            self.assertEqual(selected_option.get_attribute('innerText'), 'horror book')
            paginator = self.web_driver.find_element(By.CSS_SELECTOR, '.paginator')
            self.assertEqual(paginator.get_attribute('innerText'), '1 book')


class TestInputFilters(SeleniumTestMixin, CreateMixin, StaticLiveServerTestCase):
    shelf_model = Shelf

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self.admin = self._create_admin()

    def test_input_filters(self):
        url = reverse('admin:test_project_shelf_changelist')
        user = self._create_user()
        horror_shelf = self._create_shelf(
            name='Horror', books_type='HORROR', owner=self.admin
        )
        self._create_shelf(name='Factual', books_type='FACTUAL', owner=user)
        self.login()
        horror_result_xpath = (
            '//*[@id="result_list"]/tbody/tr/th/a[contains(text(), "Horror")]'
        )
        factual_result_xpath = (
            '//*[@id="result_list"]/tbody/tr/th/a[contains(text(), "Factual")]'
        )

        with self.subTest('Test SimpleInputFilter'):
            self.open(url)
            input_field = self._get_simple_input_filter()
            input_field.send_keys('Horror')
            self._get_filter_button().click()
            # Horror shelf is present
            self.web_driver.find_element(By.XPATH, horror_result_xpath)
            with self.assertRaises(NoSuchElementException):
                # Factual shelf is absent
                self.web_driver.find_element(By.XPATH, factual_result_xpath)
            # Both shelves should be present after clearing filter
            self.web_driver.find_element(By.CSS_SELECTOR, '.field-clear').click()
            self.web_driver.find_element(By.XPATH, horror_result_xpath)
            self.web_driver.find_element(By.XPATH, factual_result_xpath)

        with self.subTest('Test InputFilter'):
            self.open(url)
            input_field = self._get_input_filter()
            input_field.send_keys('HORROR')
            self._get_filter_button().click()
            # Horror shelf is present
            self.web_driver.find_element(By.XPATH, horror_result_xpath)
            with self.assertRaises(NoSuchElementException):
                # Factual shelf is absent
                self.web_driver.find_element(By.XPATH, factual_result_xpath)
            # Both shelves should be present after clearing filter
            self.web_driver.find_element(By.CSS_SELECTOR, '.field-clear').click()
            self.web_driver.find_element(By.XPATH, horror_result_xpath)
            self.web_driver.find_element(By.XPATH, factual_result_xpath)

        with self.subTest('Test InputFilter: UUID'):
            self.open(url)
            input_field = self.web_driver.find_element(
                By.CSS_SELECTOR, 'input[name=id__exact]'
            )
            input_field.send_keys(str(horror_shelf.id))
            self._get_filter_button().click()
            # Horror shelf is present
            self.web_driver.find_element(By.XPATH, horror_result_xpath)
            with self.assertRaises(NoSuchElementException):
                # Factual shelf is absent
                self.web_driver.find_element(By.XPATH, factual_result_xpath)
            # Both shelves should be present after clearing filter
            self.web_driver.find_element(By.CSS_SELECTOR, '.field-clear').click()
            self.web_driver.find_element(By.XPATH, horror_result_xpath)
            self.web_driver.find_element(By.XPATH, factual_result_xpath)

        with self.subTest('Test InputFilter: Related field'):
            admin_xpath = f'//*[@id="result_list"]/tbody/tr/th/a[contains(text(), "{self.admin.username}")]'
            user_xpath = f'//*[@id="result_list"]/tbody/tr/th/a[contains(text(), "{user.username}")]'
            self.open(reverse('admin:auth_user_changelist'))
            input_field = self.web_driver.find_element(
                By.XPATH,
                '//*[@id="ow-changelist-filter"]/div[1]/div/div/div[2]/div[1]/form/input',
            )
            input_field.send_keys(str(horror_shelf.id))
            self._get_filter_button().click()
            # Admin user is present
            self.web_driver.find_element(By.XPATH, admin_xpath)
            with self.assertRaises(NoSuchElementException):
                # User is absent
                self.web_driver.find_element(By.XPATH, user_xpath)
            # Both users should be present after clearing filter
            self.web_driver.find_element(By.CSS_SELECTOR, '.field-clear').click()
            self.web_driver.find_element(By.XPATH, admin_xpath)
            self.web_driver.find_element(By.XPATH, user_xpath)


class TestDashboardCharts(SeleniumTestMixin, CreateMixin, StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.admin = self._create_admin()
        self.web_driver.set_window_size(1600, 768)

    def test_pie_chart_zero_annotation(self):
        Operator.objects.all().delete()
        self.login()
        url = reverse('admin:index')
        self.open(url)
        try:
            WebDriverWait(self.web_driver, 10).until(
                EC.visibility_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        '.operator-project-distribution .annotation-text tspan',
                    )
                )
            )
        except TimeoutException:
            self.fail('Failed to find annotation text element in the chart')
        else:
            annotation_text = self.web_driver.find_element(
                By.CSS_SELECTOR, '.operator-project-distribution .annotation-text tspan'
            )
            self.assertEqual(annotation_text.text, '0')


class TestAutocompleteFilter(SeleniumTestMixin, CreateMixin, StaticLiveServerTestCase):
    shelf_model = Shelf
    book_model = Book

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self.admin = self._create_admin()
        self.login()

    def test_autocomplete_shelf_filter(self):
        url = reverse('admin:test_project_book_changelist')
        user = self._create_user()
        horror_shelf = self._create_shelf(
            name='Horror', books_type='HORROR', owner=self.admin
        )
        factual_shelf = self._create_shelf(
            name='Factual', books_type='FACTUAL', owner=user
        )
        book1 = self._create_book(name='Book 1', shelf=horror_shelf)
        book2 = self._create_book(name='Book 2', shelf=factual_shelf)
        select_id = 'id-shelf__id-dal-filter'
        filter_css_selector = f'#select2-{select_id}-container'
        filter_options = f'//*[@id="select2-{select_id}-results"]/li'
        filter_option_xpath = f'//*[@id="select2-{select_id}-results"]/li[2]'

        result_xpath = '//*[@id="result_list"]/tbody/tr/th/a[contains(text(), "{}")]'
        self.open(url)
        self.assertIn(
            (
                '<select name="shelf__id" data-dropdown-css-class="ow2-autocomplete-dropdown"'
                f' data-empty-label="-" id="{select_id}" class="admin-autocomplete'
            ),
            self.web_driver.page_source,
        )
        self.web_driver.find_element(By.CSS_SELECTOR, filter_css_selector).click()
        self.web_driver.find_element(By.CSS_SELECTOR, '.select2-container--open')
        self.assertIn(horror_shelf.name, self.web_driver.page_source)
        self.assertIn(factual_shelf.name, self.web_driver.page_source)
        self.web_driver.find_element(By.XPATH, filter_option_xpath).click()
        self.assertIn(str(factual_shelf.id), self.web_driver.current_url)
        self.web_driver.find_element(By.CSS_SELECTOR, filter_css_selector)
        self.assertNotIn(horror_shelf.name, self.web_driver.page_source)
        self.assertIn(factual_shelf.name, self.web_driver.page_source)
        with self.assertRaises(NoSuchElementException):
            # Book 1 is absent
            self.web_driver.find_element(By.XPATH, result_xpath.format(book1.name))
        # Book 2 is present
        self.web_driver.find_element(By.XPATH, result_xpath.format(book2.name))
        # "shelf" field is not nullable, therefore none option should be absent
        self.web_driver.find_element(By.CSS_SELECTOR, filter_css_selector).click()
        self.web_driver.find_element(By.CSS_SELECTOR, '.select2-container--open')
        for option in self.web_driver.find_elements(By.XPATH, filter_options):
            self.assertNotEqual(option.text, '-')

    def test_autocomplete_owner_filter(self):
        """
        Tests the null option of the AutocompleteFilter
        """
        url = reverse('admin:test_project_shelf_changelist')
        user = self._create_user()
        horror_shelf = self._create_shelf(
            name='Horror', books_type='HORROR', owner=self.admin
        )
        factual_shelf = self._create_shelf(
            name='Factual', books_type='FACTUAL', owner=user
        )
        select_id = 'id-owner_id-dal-filter'
        filter_css_selector = f'#select2-{select_id}-container'
        filter_null_option_xpath = f'//*[@id="select2-{select_id}-results"]/li[1]'
        result_xpath = '//*[@id="result_list"]/tbody/tr/th/a[contains(text(), "{}")]'
        self.open(url)
        self.assertIn(
            (
                '<select name="owner_id" data-dropdown-css-class="ow2-autocomplete-dropdown"'
                f' data-empty-label="-" id="{select_id}" class="admin-autocomplete'
            ),
            self.web_driver.page_source,
        )
        self.web_driver.find_element(By.CSS_SELECTOR, filter_css_selector).click()
        self.web_driver.find_element(By.CSS_SELECTOR, '.select2-container--open')
        self.assertIn(self.admin.username, self.web_driver.page_source)
        self.assertIn(user.username, self.web_driver.page_source)
        self.web_driver.find_element(By.XPATH, filter_null_option_xpath).click()
        self._get_filter_button().click()
        self.assertIn('owner_id__isnull=true', self.web_driver.current_url)
        with self.assertRaises(NoSuchElementException):
            # horror_shelf is absent
            self.web_driver.find_element(
                By.XPATH, result_xpath.format(horror_shelf.name)
            )
        with self.assertRaises(NoSuchElementException):
            # factual_shelf absent
            self.web_driver.find_element(
                By.XPATH, result_xpath.format(factual_shelf.name)
            )
