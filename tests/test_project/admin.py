from django.contrib import admin
from django.forms import ModelForm
from openwisp_utils.admin import (AlwaysHasChangedMixin, ReadOnlyAdmin,
                                  TimeReadonlyAdminMixin, UUIDAdmin)

from .models import Operator, Project, RadiusAccounting, Shelf


@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name']


@admin.register(RadiusAccounting)
class RadiusAccountingAdmin(ReadOnlyAdmin):
    list_display = ['session_id', 'username']
    fields = ['session_id', 'username']


class OperatorForm(AlwaysHasChangedMixin, ModelForm):
    pass


class OperatorInline(admin.StackedInline):
    model = Operator
    form = OperatorForm
    extra = 0


class ProjectAdmin(admin.ModelAdmin):
    inlines = [OperatorInline]
    list_display = ['name']
    readonly_fields = ['uuid']
    fields = ['name', 'key', 'uuid']

    class Media:
        js = ('openwisp-utils/js/uuid.js',)

admin.site.register(Operator, OperatorAdmin)
admin.site.register(RadiusAccounting, RadiusAccountingAdmin)
admin.site.register(Project, ProjectAdmin)
