from unittest.mock import patch

from django.apps import registry
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory, TestCase
from django.urls import reverse
from openwisp_utils.admin_theme.menu import (
    MenuGroup,
    MenuItem,
    MenuLink,
    register_menu_groups,
)
from openwisp_utils.utils import SortedOrderedDict


class TestMenuSchema(TestCase):
    factory = RequestFactory()
    menu_item = MenuItem(
        config={
            'model': 'test_project.Shelf',
            'name': 'changelist',
            'label': 'View Shelf',
            'icon': 'shelf-icon',
        }
    )
    menu_link = MenuLink(
        config={'label': 'test link', 'url': 'testurl.com', 'icon': 'test-icon'}
    )
    menu_group_items = {1: menu_item, 2: menu_link}
    menu_group = MenuGroup(
        config={
            'label': 'test menu group',
            'items': menu_group_items,
            'icon': 'test-icon',
        }
    )

    def _get_menu_item_config(
        self,
        label='test label',
        model='test_project.Shelf',
        name='add',
        icon='test_icon',
    ):
        return {'label': label, 'model': model, 'name': name, 'icon': icon}

    def _get_menu_link_config(
        self, label='test label', url='testurl.com', icon='test-icon'
    ):
        return {'label': label, 'url': url, 'icon': icon}

    def _get_menu_group_config(
        slef, label='test label', items=menu_group_items, icon='test icon'
    ):
        return {
            'label': label,
            'items': items,
            'icon': icon,
        }

    @patch('openwisp_utils.admin_theme.menu.MENU', SortedOrderedDict())
    def test_register_menu_grouplabel(self):
        from openwisp_utils.admin_theme.menu import MENU

        items_order = [self.menu_item, self.menu_group, self.menu_link]
        test_menu_groups = {1: self.menu_item, 3: self.menu_link, 2: self.menu_group}
        register_menu_groups(test_menu_groups)

        with self.subTest('Test ordering of menu groups'):
            current_item_index = 0
            for item in MENU.values():
                self.assertEqual(item, items_order[current_item_index])
                current_item_index += 1

        with self.subTest('Registering at an occupied position'):
            with self.assertRaises(ValueError):
                register_menu_groups({1: self.menu_link})

        with self.subTest('Registering with invalid position'):
            with self.assertRaises(ImproperlyConfigured):
                register_menu_groups({'invalid_position': self.menu_group})

        with self.subTest('Registering with invalid type'):
            with self.assertRaises(ValueError):
                register_menu_groups({10: []})

        with self.subTest('Registering with invalid groups'):
            with self.assertRaises(ImproperlyConfigured):
                register_menu_groups([])

    def test_menu_link(self):
        with self.subTest('Menu Link with invalid config'):
            with self.assertRaises(ImproperlyConfigured):
                MenuLink(config=[])

        with self.subTest('Menu Link without label'):
            with self.assertRaises(ValueError):
                _config = self._get_menu_link_config(label=None)
                MenuLink(config=_config)

        with self.subTest('Menu Link without url'):
            with self.assertRaises(ValueError):
                _config = self._get_menu_link_config(url=None)
                MenuLink(config=_config)

        with self.subTest('Menu Link with invalid label'):
            with self.assertRaises(ValueError):
                _config = self._get_menu_link_config(label=123)
                MenuLink(config=_config)

        with self.subTest('Menu Link with invalid url'):
            with self.assertRaises(ValueError):
                _config = self._get_menu_link_config(url=123)
                MenuLink(config=_config)

        with self.subTest('Menu Link test create context'):
            _config = self._get_menu_link_config()
            menu_link = MenuLink(config=_config)
            context = menu_link.create_context()
            self.assertEqual(context.get('label'), _config['label'])
            self.assertEqual(context.get('url'), _config['url'])
            self.assertEqual(context.get('icon'), _config['icon'])

        with self.subTest('Menu Link without icon'):
            _config = self._get_menu_link_config(icon=None)
            menu_link = MenuLink(config=_config)
            context = menu_link.create_context()
            self.assertEqual(context.get('icon'), None)

    def test_menu_item(self):

        with self.subTest('Menu Item without name'):
            _config = self._get_menu_item_config(name=None)
            with self.assertRaises(ValueError):
                MenuItem(config=_config)

        with self.subTest('Menu Item with invalid name'):
            _config = self._get_menu_item_config(name=123)
            with self.assertRaises(ValueError):
                MenuItem(config=_config)

        with self.subTest('Menu Item with invalid config'):
            with self.assertRaises(ImproperlyConfigured):
                MenuItem(config=[])

        with self.subTest('Menu Item without model'):
            _config = self._get_menu_item_config(model=None)
            with self.assertRaises(ValueError):
                MenuItem(config=_config)

        with self.subTest('Menu Item with invalid model'):
            _config = self._get_menu_item_config(model=123)
            with self.assertRaises(ValueError):
                MenuItem(config=_config)

    def test_menu_item_access(self):
        url = reverse('admin:index')
        request = self.factory.get(url)
        user = get_user_model().objects.create_superuser(
            username='administrator', password='admin', email='test@test.org'
        )
        request.user = user
        _config = self._get_menu_item_config()
        menu_item = MenuItem(config=_config)

        with self.subTest('Menu Item with label and icon'):
            context = menu_item.get_context(request=request)
            self.assertEqual(context.get('label'), _config['label'])
            self.assertEqual(context.get('icon'), _config['icon'])

        with self.subTest('Menu Item without label and icon'):
            _config = self._get_menu_item_config(label=None, icon=None)
            menu_item = MenuItem(config=_config)
            context = menu_item.get_context(request=request)
            app_label, model = _config['model'].split('.')
            model_class = registry.apps.get_model(app_label, model)
            label = f'{model_class._meta.verbose_name_plural} {_config["name"]}'
            self.assertEqual(context.get('label'), label)
            self.assertEqual(context.get('icon'), None)

        # testing with user having no access
        user = get_user_model().objects.create(
            username='operator',
            password='pass',
            email='email@email',
            is_staff=True,
            is_superuser=False,
        )
        request.user = user
        with self.subTest('Menu Item context when user do not have access'):
            context = menu_item.get_context(request)
            self.assertEqual(context, None)

    def test_menu_group(self):

        with self.subTest('Menu Group with invalid config'):
            with self.assertRaises(ImproperlyConfigured):
                MenuGroup(config=[])

        with self.subTest('Menu Group without label'):
            with self.assertRaises(ValueError):
                _config = self._get_menu_group_config(label=None)
                MenuGroup(config=_config)

        with self.subTest('Menu Group with invalid label'):
            with self.assertRaises(ValueError):
                _config = self._get_menu_group_config(label=1234)
                MenuGroup(config=_config)

        with self.subTest('Menu Group without items'):
            with self.assertRaises(ValueError):
                _config = self._get_menu_group_config(items=None)
                MenuGroup(config=_config)

        with self.subTest('Menu Group with invalid items type'):
            with self.assertRaises(ValueError):
                _config = self._get_menu_group_config(items=[])
                MenuGroup(config=_config)

        with self.subTest('Menu Group with invalid items position'):
            with self.assertRaises(ImproperlyConfigured):
                _config = self._get_menu_group_config(items={'1': self.menu_link})
                MenuGroup(config=_config)

        with self.subTest('Menu Group with invalid items type'):
            with self.assertRaises(ValueError):
                _config = self._get_menu_group_config(items={1: []})
                MenuGroup(config=_config)

        with self.subTest('Menu Group items ordering test'):
            menu_group_items = {2: self.menu_item, 1: self.menu_link}
            menu_group_items_order = [self.menu_link, self.menu_item]
            _config = self._get_menu_group_config(items=menu_group_items)
            menu_group = MenuGroup(config=_config)
            current_item_index = 0
            for item in menu_group.items.values():
                self.assertEqual(item, menu_group_items_order[current_item_index])
                current_item_index += 1

        url = reverse('admin:index')
        request = self.factory.get(url)
        user = get_user_model().objects.create_superuser(
            username='administrator', password='admin', email='test@test.org'
        )
        request.user = user
        with self.subTest('Menu Group with icon'):
            _config = self._get_menu_group_config()
            menu_group = MenuGroup(config=_config)
            context = menu_group.get_context(request=request)
            self.assertEqual(context.get('icon'), _config['icon'])

        with self.subTest('Menu Group without icon'):
            _config = self._get_menu_group_config(icon=None)
            menu_group = MenuGroup(config=_config)
            context = menu_group.get_context(request=request)
            self.assertEqual(context.get('icon'), None)

        # testing with user having no access
        user = get_user_model().objects.create(
            username='operator',
            password='pass',
            email='email@email',
            is_staff=True,
            is_superuser=False,
        )
        request.user = user
        with self.subTest('Menu Group content when user have no access of items'):
            _items = {1: self.menu_item}
            _config = self._get_menu_group_config(items=_items)
            menu_group = MenuGroup(config=_config)
            context = menu_group.get_context(request=request)
            self.assertEqual(context, None)

        with self.subTest('Menu Group content when user have no access of some items'):
            _items = {1: self.menu_item, 2: self.menu_link}
            _config = self._get_menu_group_config(items=_items)
            menu_group = MenuGroup(config=_config)
            context = menu_group.get_context(request=request)
            context_items = context.get('sub_items')
            link_context = self.menu_link.get_context()
            self.assertEqual(len(context_items), 1)
            self.assertEqual(context_items[0].get('label'), link_context.get('label'))
            self.assertEqual(context_items[0].get('url'), link_context.get('url'))
