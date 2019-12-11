import openwisp_users.models
from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext_lazy
from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from openwisp_users.models import (Group, Organization, OrganizationOwner, OrganizationUser,User)
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.admin import User
from django.contrib.sites.models import Site
from test_project.admin import (ProjectAdmin,OperatorAdmin,RadiusAccountingAdmin)
from test_project.models import Operator, Project, RadiusAccounting
User = get_user_model()

class MyAdminSite(AdminSite):
     # link to frontend
    site_url = None

    ## <title>
    site_title = getattr(settings,
                          'OPENWISP_ADMIN_SITE_TITLE',
                          'OpenWISP Admin')

    # h1 text
    site_header = getattr(settings,
                            'OPENWISP_ADMIN_SITE_HEADER',
                            'OPENWISP')
    
    # text at the top of the admin index page
    index_title = ugettext_lazy(
          getattr(settings,
                'OPENWISP_ADMIN_INDEX_TITLE',
                'Network administration')
    )

admin_site = MyAdminSite(name='admin')

#Models registered for Users And Organizations
admin_site.register(User)
admin_site.register(Group)
admin_site.register(Organization)
admin_site.register(OrganizationOwner)
admin_site.register(OrganizationUser)

#Models registered for Sites
admin_site.register(Site)

#Models registered for test_project
admin_site.register(Operator, OperatorAdmin)
admin_site.register(RadiusAccounting, RadiusAccountingAdmin)
admin_site.register(Project, ProjectAdmin)
