from datetime import timedelta

from django.contrib import admin
from django.contrib.admin.filters import SimpleListFilter
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from openwisp_utils.admin import (
    AlwaysHasChangedMixin,
    CopyableFieldsAdmin,
    HelpTextStackedInline,
    ReadOnlyAdmin,
    ReceiveUrlAdmin,
    TimeReadonlyAdminMixin,
)
from openwisp_utils.admin_theme.filters import (
    AutocompleteFilter,
    InputFilter,
    SimpleInputFilter,
    SubFilterMixin,
)

from .models import (
    Book,
    Operator,
    OrganizationRadiusSettings,
    Project,
    RadiusAccounting,
    Shelf,
)

admin.site.unregister(User)


class AutoShelfFilter(AutocompleteFilter):
    title = _("shelf")
    field_name = "shelf"
    parameter_name = "shelf__id"


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["username", "is_staff", "is_superuser", "is_active"]
    list_filter = [
        ("username", InputFilter),
        ("shelf", InputFilter),
        "is_staff",
        "is_superuser",
        "is_active",
    ]
    search_fields = ("username",)


class CreatedSubFilter(SubFilterMixin, SimpleListFilter):
    title = _("Created date")
    parameter_name = "created"
    parent_parameter_name = "shelf__books_type"
    parent_active_values = ("HORROR",)

    def lookups(self, request, model_admin):
        return (
            ("today", _("Today")),
            ("past_7_days", _("Past 7 days")),
            ("has_date", _("Has date")),
        )

    def filter_queryset(self, request, queryset):
        value = self.value()
        now = timezone.localtime(timezone.now())
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if value == "today":
            return queryset.filter(
                created__gte=today_start,
                created__lt=today_start + timedelta(days=1),
            )
        elif value == "past_7_days":
            return queryset.filter(
                created__gte=today_start - timedelta(days=7),
                created__lt=today_start + timedelta(days=1),
            )
        elif value == "has_date":
            return queryset.exclude(created__isnull=True)
        return queryset


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_filter = [
        AutoShelfFilter,
        "shelf__books_type",
        CreatedSubFilter,
        "name",
    ]
    search_fields = ["name"]


@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name"]
    list_filter = ["project__name"]  # DO NOT CHANGE: used for testing filters


@admin.register(RadiusAccounting)
class RadiusAccountingAdmin(ReadOnlyAdmin):
    list_display = ["session_id", "username"]
    fields = ["session_id", "username"]


class OperatorForm(AlwaysHasChangedMixin, ModelForm):
    pass


class OperatorInline(HelpTextStackedInline):
    model = Operator
    form = OperatorForm
    extra = 0
    help_text = {
        "text": _("Only added operators will have permission to access the project."),
        "documentation_url": "https://github.com/openwisp/openwisp-utils/",
    }


@admin.register(Project)
class ProjectAdmin(CopyableFieldsAdmin, ReceiveUrlAdmin):
    inlines = [OperatorInline]
    list_display = ("name",)
    fields = ("uuid", "name", "key", "receive_url")
    readonly_fields = ("receive_url",)
    receive_url_name = "receive_project"
    copyable_fields = ("uuid",)


class ShelfFilter(SimpleInputFilter):
    parameter_name = "shelf"
    title = _("Shelf")

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(name__icontains=self.value())


class ReverseBookFilter(AutocompleteFilter):
    title = _("Book")
    field_name = "book"
    parameter_name = "book"


class AutoOwnerFilter(AutocompleteFilter):
    title = _("owner")
    field_name = "owner"
    parameter_name = "owner_id"


@admin.register(Shelf)
class ShelfAdmin(TimeReadonlyAdminMixin, admin.ModelAdmin):
    # DO NOT CHANGE: used for testing filters
    list_filter = [
        ShelfFilter,
        ["books_type", InputFilter],
        ["id", InputFilter],
        AutoOwnerFilter,
        "books_type",
        ReverseBookFilter,
    ]
    search_fields = ["name"]


@admin.register(OrganizationRadiusSettings)
class OrganizationRadiusSettingsAdmin(admin.ModelAdmin):
    pass
