from django.contrib import admin
from django.forms import ModelForm
from openwisp_utils.admin import AlwaysHasChangedMixin, ReadOnlyAdmin

from .models import Operator, Project, RadiusAccounting


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


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    inlines = [OperatorInline]
    list_display = ['name']
