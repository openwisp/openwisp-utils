from django.contrib.admin import ModelAdmin
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


class TimeReadonlyAdminMixin(object):
    """
    mixin that automatically flags
    `created` and `modified` as readonly
    """
    def __init__(self, *args, **kwargs):
        self.readonly_fields += ('created', 'modified',)
        super().__init__(*args, **kwargs)


class ReadOnlyAdmin(ModelAdmin):
    """
    Disables all editing capabilities
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.readonly_fields = [f.name for f in self.model._meta.fields]

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:  # pragma: no cover
            del actions['delete_selected']
        return actions

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):  # pragma: nocover
        pass

    def delete_model(self, request, obj):  # pragma: nocover
        pass

    def save_related(self, request, form, formsets, change):  # pragma: nocover
        pass

    def change_view(self, request, object_id, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save'] = False
        return super().change_view(request, object_id, extra_context=extra_context)


class AlwaysHasChangedMixin(object):
    def has_changed(self):
        """
        This django-admin trick ensures the settings
        are saved even if default values are unchanged
        (without this trick new setting objects won't be
        created unless users change the default values)
        """
        if self.instance._state.adding:
            return True
        return super().has_changed()


class UUIDAdmin(object):
    """
    Defines a field name uuid whose value is that
    of the id of the object
    """
    def uuid(self, obj):
        return obj.pk

    uuid.short_description = _('UUID')


class GetUrlAdmin(object):
    """
    Return a receive_url field whose value is that of
    a view_name concatenated with the obj id and/or
    with the key of the obj
    """
    def receive_url(self, obj, view_name, key=False):
        """
        :param view_name: The name of the view usually an api
        :param key: determines if the key should be added or not
        """
        url = reverse('{0}'.format(view_name), kwargs={'pk': obj.pk})
        if key:
            return '{0}?key={1}'.format(url, obj.key)
        else:
            return url

    receive_url.short_description = _('Url')
