from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework import generics, viewsets

from openwisp_utils.api.pagination import OpenWispPagination

from ..models import Project, Shelf
from ..serializers import ShelfSerializer


class ReceiveProjectView(View):
    """Test View.

    Test view is used to check the validity of the pk and the key. It
    returns the project name.
    """

    def get(self, request, pk):
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return JsonResponse({"detail": _("project not found")}, status=400)
        key = request.GET.get("key")
        if project.key != key:
            return JsonResponse({"detail": _("wrong key")}, status=403)
        return JsonResponse({"detail": _("ok"), "name": project.name}, status=200)


class ShelfListCreateView(generics.ListCreateAPIView):
    queryset = Shelf.objects.all()
    serializer_class = ShelfSerializer


class ShelfRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Shelf.objects.all()
    serializer_class = ShelfSerializer


class ShelfViewSet(viewsets.ModelViewSet):
    """ViewSet for Shelf model with OpenWispPagination."""

    queryset = Shelf.objects.order_by("-created_at")
    serializer_class = ShelfSerializer
    pagination_class = OpenWispPagination


receive_project = ReceiveProjectView.as_view()
shelf_list_create_view = ShelfListCreateView.as_view()
shelf_retrieve_update_destroy_view = ShelfRetrieveUpdateDestroyView.as_view()
