from django.contrib import admin
from django.contrib.auth.models import User
from django.forms import ModelForm
from openwisp_utils.admin import (
    AlwaysHasChangedMixin,
    ReadOnlyAdmin,
    ReceiveUrlAdmin,
    TimeReadonlyAdminMixin,
    UUIDAdmin,
)

from .models import Operator, Project, RadiusAccounting, Shelf

admin.site.unregister(User)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'is_staff', 'is_superuser', 'is_active']
    list_filter = ['username', 'is_staff', 'is_superuser', 'is_active']


@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name']
    list_filter = ['project__name']


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
class ProjectAdmin(UUIDAdmin, ReceiveUrlAdmin):
    inlines = [OperatorInline]
    list_display = ('name',)
    fields = ('uuid', 'name', 'key', 'receive_url')
    readonly_fields = ('uuid', 'receive_url')
    receive_url_name = 'receive_project'


@admin.register(Shelf)
class ShelfAdmin(TimeReadonlyAdminMixin, admin.ModelAdmin):
    list_filter = (
        'books_type',
        'name',
        'owner__username',
        'owner__is_staff',
        'owner__is_active',
        'locked',
        'books_count',
        'created_at',
    )
