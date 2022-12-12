from openwisp_users.api.authentication import BearerAuthentication
from openwisp_users.api.permissions import DjangoModelPermissions
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated


class ProtectedAPIMixin(object):
    authentication_classes = [BearerAuthentication, SessionAuthentication]
    permission_classes = [
        IsAuthenticated,
        DjangoModelPermissions,
    ]
