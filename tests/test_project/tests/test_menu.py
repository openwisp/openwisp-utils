from unittest.mock import patch

from django.apps import registry
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from openwisp_utils.admin_theme.menu import (
    MenuGroup,
    MenuLink,
    ModelLink,
    register_menu_group,
    register_menu_subitem,
)
from openwisp_utils.utils import SortedOrderedDict


class TestMenuSchema(TestCase):
    factory = RequestFactory()

    def _get_model_link_config(
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

    def _get_menu_group_config(self, label='test label', items=None, icon='test icon'):
        if items is None:
            # set default items
            model_link = self._get_model_link_config()
            menu_link = self._get_menu_link_config()
            items = {1: menu_link, 2: model_link}
        return {
            'label': label,
            'items': items,
            'icon': icon,
        }

    @patch('openwisp_utils.admin_theme.menu.MENU', SortedOrderedDict())
    def test_register_menu_groups(self):

        from openwisp_utils.admin_theme.menu import MENU

        # create a menu
        model_link_config = self._get_model_link_config()
        menu_link_config = self._get_menu_link_config()
        menu_group_config = self._get_menu_group_config()
        test_menu_groups = {
            3: menu_group_config,
            2: model_link_config,
            1: menu_link_config,
        }
        # save menu order to compare
        items_order = [
            MenuLink(config=menu_link_config),
            ModelLink(config=model_link_config),
            MenuGroup(config=menu_group_config),
        ]
        user = get_user_model().objects.create_superuser(
            username='administrator', password='admin', email='test@test.org'
        )
        self.client.force_login(user)
        url = reverse('admin:index')
        for position, config in test_menu_groups.items():
            register_menu_group(position=position, config=config)

        with self.subTest('Test ordering of menu groups'):
            request = self.factory.get(url)
            request.user = user
            current_item_index = 0
            for item in MENU.values():
                item_context = item.get_context(request)
                ordered_item_context = items_order[current_item_index].get_context(
                    request
                )
                self.assertEqual(item_context, ordered_item_context)
                current_item_index += 1

        with self.subTest('Registering at an occupied position'):
            with self.assertRaises(ImproperlyConfigured):
                register_menu_group(position=1, config=model_link_config)

        with self.subTest('Registering with invalid position'):
            with self.assertRaises(ImproperlyConfigured):
                register_menu_group(
                    position='invalid_position', config=menu_link_config
                )

        with self.subTest('Registering with invalid config'):
            with self.assertRaises(ImproperlyConfigured):
                register_menu_group(position=-1, config=[])

        with self.subTest('Registering with unknow menu group'):
            with self.assertRaises(ImproperlyConfigured):
                register_menu_group(position=-1, config={})

        with self.subTest('Model Link with invalid name'):
            _config = self._get_model_link_config(name="invalid_name")
            with self.assertRaises(NoReverseMatch):
                register_menu_group(position=-1, config=_config)
                self.client.get(url)

        with self.subTest('Model Group with invalid name in item'):
            _config = self._get_menu_group_config(
                items={1: self._get_model_link_config(name="invalid_name")}
            )
            with self.assertRaises(NoReverseMatch):
                register_menu_group(position=-2, config=_config)
                self.client.get(url)

    @patch('openwisp_utils.admin_theme.menu.MENU', SortedOrderedDict())
    def test_register_menu_subitem(self):
        from openwisp_utils.admin_theme.menu import MENU

        config = self._get_menu_link_config()
        register_menu_group(position=100, config=self._get_menu_group_config())
        register_menu_group(position=102, config=self._get_menu_link_config())
        with self.subTest('Test menu subitem with invalid group position'):
            with self.assertRaises(ImproperlyConfigured):
                register_menu_subitem(
                    group_position='invalid', item_position=1, config=config
                )

        with self.subTest('Test menu subitem with invalid item position'):
            with self.assertRaises(ImproperlyConfigured):
                register_menu_subitem(
                    group_position=100, item_position='invalid', config=config
                )
        with self.subTest('Test menu subitem with wrong group positions or config'):
            with self.assertRaises(ImproperlyConfigured):
                register_menu_subitem(
                    group_position=101, item_position=1, config=config
                )
            with self.assertRaises(ImproperlyConfigured):
                register_menu_subitem(group_position=100, item_position=1, config=[])
            with self.assertRaises(ImproperlyConfigured):
                register_menu_subitem(
                    group_position=100, item_position=1, config=config
                )
            with self.assertRaises(ImproperlyConfigured):
                register_menu_subitem(
                    group_position=102, item_position=1, config=config
                )
            with self.assertRaises(ImproperlyConfigured):
                register_menu_subitem(
                    group_position=100,
                    item_position=3,
                    config=self._get_menu_group_config(),
                )

        with self.subTest('Test menu subitem with valid data'):
            model_link_config = self._get_model_link_config()
            register_menu_subitem(group_position=100, item_position=3, config=config)
            register_menu_subitem(
                group_position=100, item_position=4, config=model_link_config
            )
            user = get_user_model().objects.create_superuser(
                username='administrator', password='admin', email='test@test.org'
            )
            url = reverse('admin:index')
            request = self.factory.get(url)
            request.user = user
            item = MenuLink(config=config)
            item_context = item.get_context(request)
            registered_item_context = MENU[100].items[3].get_context(request)
            self.assertEqual(registered_item_context, item_context)
            model_link_item = ModelLink(config=model_link_config)
            model_link_context = model_link_item.get_context(request)
            registered_model_context = MENU[100].items[4].get_context(request)
            self.assertEqual(model_link_context, registered_model_context)

    def test_menu_link(self):

        with self.subTest('Menu Link with invalid config'):
            with self.assertRaises(ImproperlyConfigured):
                MenuLink(config=[])

        with self.subTest('Menu Link without label'):
            with self.assertRaises(ImproperlyConfigured):
                _config = self._get_menu_link_config(label=None)
                MenuLink(config=_config)

        with self.subTest('Menu Link without url'):
            with self.assertRaises(ImproperlyConfigured):
                _config = self._get_menu_link_config(url=None)
                MenuLink(config=_config)

        with self.subTest('Menu Link with invalid url'):
            with self.assertRaises(ImproperlyConfigured):
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

        with self.subTest('Menu Link test mailto'):
            mailto = 'mailto:test@test.com'
            _config = self._get_menu_link_config(url=mailto)
            menu_link = MenuLink(config=_config)
            context = menu_link.create_context()
            self.assertEqual(context.get('url'), mailto)

    def test_model_link(self):

        with self.subTest('Model Link without name'):
            _config = self._get_model_link_config(name=None)
            with self.assertRaises(ImproperlyConfigured):
                ModelLink(config=_config)

        with self.subTest('Model Link with invalid name'):
            _config = self._get_model_link_config(name=123)
            with self.assertRaises(ImproperlyConfigured):
                ModelLink(config=_config)

        with self.subTest('Model Link with invalid config'):
            with self.assertRaises(ImproperlyConfigured):
                ModelLink(config=[])

        with self.subTest('Model Link without model'):
            _config = self._get_model_link_config(model=None)
            with self.assertRaises(ImproperlyConfigured):
                ModelLink(config=_config)

        with self.subTest('Model Link with invalid model'):
            _config = self._get_model_link_config(model=123)
            with self.assertRaises(ImproperlyConfigured):
                ModelLink(config=_config)

    def test_model_link_access(self):
        url = reverse('admin:index')
        request = self.factory.get(url)
        user = get_user_model().objects.create_superuser(
            username='administrator', password='admin', email='test@test.org'
        )
        request.user = user
        _config = self._get_model_link_config()
        model_link = ModelLink(config=_config)

        with self.subTest('Model Link with label and icon'):
            context = model_link.get_context(request=request)
            self.assertEqual(context.get('label'), _config['label'])
            self.assertEqual(context.get('icon'), _config['icon'])

        with self.subTest('Model Link without label and icon'):
            _config = self._get_model_link_config(label=None, icon=None)
            model_link = ModelLink(config=_config)
            context = model_link.get_context(request=request)
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
        with self.subTest('Model Link context when user do not have access'):
            context = model_link.get_context(request)
            self.assertEqual(context, None)

    def test_menu_group(self):

        with self.subTest('Menu Group with invalid config'):
            with self.assertRaises(ImproperlyConfigured):
                MenuGroup(config=[])

        with self.subTest('Menu Group without label'):
            with self.assertRaises(ImproperlyConfigured):
                _config = self._get_menu_group_config(label=None)
                MenuGroup(config=_config)

        with self.subTest('Menu Group without items'):
            with self.assertRaises(ImproperlyConfigured):
                MenuGroup(config={'label': "test label"})

        with self.subTest('Menu Group with invalid items type'):
            with self.assertRaises(ImproperlyConfigured):
                _config = self._get_menu_group_config(items=[])
                MenuGroup(config=_config)

        with self.subTest('Menu Group with unknown item'):
            with self.assertRaises(ImproperlyConfigured):
                _config = self._get_menu_group_config(items={1: {}})
                MenuGroup(config=_config)

        with self.subTest('Menu Group with invalid items position'):
            with self.assertRaises(ImproperlyConfigured):
                _config = self._get_menu_group_config(
                    items={'1': self._get_menu_link_config()}
                )
                MenuGroup(config=_config)

        with self.subTest('Menu Group with invalid items type'):
            with self.assertRaises(ImproperlyConfigured):
                _config = self._get_menu_group_config(items={1: []})
                MenuGroup(config=_config)

        url = reverse('admin:index')
        request = self.factory.get(url)
        user = get_user_model().objects.create_superuser(
            username='administrator', password='admin', email='test@test.org'
        )
        request.user = user
        with self.subTest('Menu Group items ordering test'):
            link_config = self._get_menu_link_config()
            model_link_config = self._get_model_link_config()
            menu_group_items = {2: model_link_config, 1: link_config}
            # save order
            menu_group_items_order = [
                MenuLink(config=link_config),
                ModelLink(config=model_link_config),
            ]
            _config = self._get_menu_group_config(items=menu_group_items)
            menu_group = MenuGroup(config=_config)
            current_item_index = 0
            for item in menu_group.items.values():
                item_context = item.get_context(request)
                ordered_item_context = menu_group_items_order[
                    current_item_index
                ].get_context(request)
                self.assertEqual(item_context, ordered_item_context)
                current_item_index += 1

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

        with self.subTest(
            'Test superuser access to all model links present in menu group'
        ):
            add_link_config = self._get_model_link_config(name='add')
            change_link_config = self._get_model_link_config(name='changelist')
            items = {1: add_link_config, 2: change_link_config}
            menu_group_config = self._get_menu_group_config(items=items)
            menu_group = MenuGroup(config=menu_group_config)
            context = menu_group.create_context(request=request)
            sub_items = context.get('sub_items')
            self.assertEqual(len(sub_items), 2)

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
            _items = {1: self._get_model_link_config()}
            _config = self._get_menu_group_config(items=_items)
            menu_group = MenuGroup(config=_config)
            context = menu_group.get_context(request=request)
            self.assertEqual(context, None)

        with self.subTest('Menu Group content when user have no access of some items'):
            link_config = (
                self._get_menu_link_config()
            )  # user have permission to see this link
            _items = {1: self._get_model_link_config(), 2: link_config}
            _config = self._get_menu_group_config(items=_items)
            menu_group = MenuGroup(config=_config)
            context = menu_group.get_context(request=request)
            context_items = context.get('sub_items')
            link = MenuLink(config=link_config)
            link_context = link.get_context()
            self.assertEqual(len(context_items), 1)
            self.assertEqual(context_items[0].get('label'), link_context.get('label'))
            self.assertEqual(context_items[0].get('url'), link_context.get('url'))
