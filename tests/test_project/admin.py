from django.contrib import admin
from django.forms import ModelForm
from openwisp_utils.admin import (AlwaysHasChangedMixin, ReadOnlyAdmin,
                                  UUIDAdmin)

from .models import Operator, Project, RadiusAccounting


class OperatorAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name']


class RadiusAccountingAdmin(ReadOnlyAdmin):
    list_display = ['session_id', 'username']
    fields = ['session_id', 'username']


class OperatorForm(AlwaysHasChangedMixin, ModelForm):
    pass


class OperatorInline(admin.StackedInline):
    model = Operator
    form = OperatorForm
    extra = 0


class ProjectAdmin(admin.ModelAdmin, UUIDAdmin):
    inlines = [OperatorInline]
    list_display = ['name']
    readonly_fields = ['uuid']
    fields = ['name', 'key', 'uuid']

    class Media:
        js = ('openwisp-utils/js/uuid.js',)

    def _get_fields(self, fields, request, obj=None):
        """
        removes readonly_fields in add view
        """
        if obj:
            return fields
        new_fields = fields[:]
        for field in self.readonly_fields:
            if field in new_fields:
                new_fields.remove(field)
        return new_fields

    def get_fields(self, request, obj=None):
        return self._get_fields(self.fields, request, obj)

    def get_readonly_fields(self, request, obj=None):
        return self._get_fields(self.readonly_fields, request, obj)


admin.site.register(Operator, OperatorAdmin)
admin.site.register(RadiusAccounting, RadiusAccountingAdmin)
admin.site.register(Project, ProjectAdmin)
