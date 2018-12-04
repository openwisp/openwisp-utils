from django.contrib import admin
from openwisp_utils.admin import ReadOnlyAdmin

from .models import RadiusAccounting


class RadiusAccountingAdmin(ReadOnlyAdmin):
    list_display = ['session_id', 'username']
    fields = ['session_id', 'username']


admin.site.register(RadiusAccounting, RadiusAccountingAdmin)
