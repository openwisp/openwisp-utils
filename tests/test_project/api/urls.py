from django.urls import path, re_path

from . import views

urlpatterns = [
    re_path(
        r"^receive_project/(?P<pk>[^/\?]+)/$",
        views.receive_project,
        name="receive_project",
    ),
    path("shelves/", views.shelf_list_create_view, name="shelf_list"),
    path(
        "shelves/<uuid:pk>/",
        views.shelf_retrieve_update_destroy_view,
        name="shelf_detail",
    ),
]
