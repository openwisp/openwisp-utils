from django.urls import re_path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"shelves", views.ShelfViewSet, basename="shelf")

urlpatterns = [
    re_path(
        r"^receive_project/(?P<pk>[^/\?]+)/$",
        views.receive_project,
        name="receive_project",
    ),
    *router.urls,
]
