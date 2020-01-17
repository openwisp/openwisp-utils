from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^receive_project/(?P<pk>[^/\?]+)/$',
        views.receive_project,
        name='receive_project'),
]
