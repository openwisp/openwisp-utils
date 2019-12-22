from django.contrib import admin
from django.forms import ModelForm
from openwisp_utils.admin import (AlwaysHasChangedMixin, ReadOnlyAdmin,
                                  TimeReadonlyAdminMixin)
from openwisp_utils.admin_theme.site import admin_site

from .models import Operator, Project, RadiusAccounting, Shelf


@admin.register(Operator, site=admin_site)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name']


@admin.register(RadiusAccounting, site=admin_site)
class RadiusAccountingAdmin(ReadOnlyAdmin):
    list_display = ['session_id', 'username']
    fields = ['session_id', 'username']


class OperatorForm(AlwaysHasChangedMixin, ModelForm):
    pass


class OperatorInline(admin.StackedInline):
    model = Operator
    form = OperatorForm
    extra = 0


@admin.register(Project, site=admin_site)
class ProjectAdmin(admin.ModelAdmin):
    inlines = [OperatorInline]
    list_display = ['name']


@admin.register(Shelf, site=admin_site)
class ShelfAdmin(TimeReadonlyAdminMixin, admin.ModelAdmin):
    pass
