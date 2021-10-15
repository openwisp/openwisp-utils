from django.contrib.admin import ModelAdmin, StackedInline
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class TimeReadonlyAdminMixin(object):
    """
    mixin that automatically flags
    `created` and `modified` as readonly
    """

    def __init__(self, *args, **kwargs):
        self.readonly_fields += ('created', 'modified')
        super().__init__(*args, **kwargs)


class ReadOnlyAdmin(ModelAdmin):
    """
    Disables all editing capabilities
    """

    exclude = tuple()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        exclude = self.exclude
        self.readonly_fields = [
            f.name for f in self.model._meta.fields if f.name not in exclude
        ]

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
        This django-admin trick ensures the inline item
        is saved even if default values are unchanged
        (without this trick new objects won't be
        created unless users change the default values)
        """
        if self.instance._state.adding:
            return True
        return super().has_changed()


class UUIDAdmin(ModelAdmin):
    """
    Defines a field name uuid whose value is that
    of the id of the object
    """

    def uuid(self, obj):
        return obj.pk

    def _process_fields(self, fields, request, obj):
        fields = list(fields)
        if 'uuid' in fields and not obj:
            fields.remove('uuid')
        if 'uuid' not in fields and obj:
            fields.insert(0, 'uuid')
        return tuple(fields)

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        return self._process_fields(fields, request, obj)

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        return self._process_fields(fields, request, obj)

    class Media:
        js = ('admin/js/jquery.init.js', 'openwisp-utils/js/uuid.js')

    uuid.short_description = _('UUID')


class ReceiveUrlAdmin(ModelAdmin):
    """
    Return a receive_url field whose value is that of
    a view_name concatenated with the obj id and/or
    with the key of the obj
    """

    receive_url_querystring_arg = 'key'
    receive_url_object_arg = 'pk'
    receive_url_name = None
    receive_url_urlconf = None
    receive_url_baseurl = None

    def add_view(self, request, *args, **kwargs):
        self.request = request
        return super().add_view(request, *args, **kwargs)

    def change_view(self, request, *args, **kwargs):
        self.request = request
        return super().change_view(request, *args, **kwargs)

    def receive_url(self, obj):
        """
        :param obj: Object for which the url is generated
        """
        if self.receive_url_name is None:
            raise ValueError('receive_url_name is not set up')
        reverse_kwargs = {}
        if self.receive_url_object_arg:
            reverse_kwargs = {
                self.receive_url_object_arg: getattr(obj, self.receive_url_object_arg)
            }
        receive_path = reverse(
            self.receive_url_name,
            urlconf=self.receive_url_urlconf,
            kwargs=reverse_kwargs,
        )
        baseurl = self.receive_url_baseurl
        if not baseurl:
            baseurl = '{0}://{1}'.format(self.request.scheme, self.request.get_host())
        if self.receive_url_querystring_arg:
            url = '{0}{1}?{2}={3}'.format(
                baseurl,
                receive_path,
                self.receive_url_querystring_arg,
                getattr(obj, self.receive_url_querystring_arg),
            )
        return url

    class Media:
        js = ('admin/js/jquery.init.js', 'openwisp-utils/js/receive_url.js')

    receive_url.short_description = _('URL')


class HelpTextStackedInline(StackedInline):
    help_text = None
    template = 'admin/edit_inline/help_text_stacked.html'

    class Media:
        css = {'all': ['admin/css/help-text-stacked.css']}

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.help_text = self.help_text
        return formset
