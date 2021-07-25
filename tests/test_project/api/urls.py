from django.urls import re_path

from . import views

urlpatterns = [
    re_path(
        r'^receive_project/(?P<pk>[^/\?]+)/$',
        views.receive_project,
        name='receive_project',
    )
]
