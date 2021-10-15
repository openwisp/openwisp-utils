from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views import View

from ..models import Project


class ReceiveProjectView(View):
    """
    This test view allows to check the validity of the pk and the key, and receive project name
    Required query string parameters:
        * key
    """

    def get(self, request, pk):
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return JsonResponse({'detail': _('project not found')}, status=400)
        key = request.GET.get('key')
        if project.key != key:
            return JsonResponse({'detail': _('wrong key')}, status=403)
        return JsonResponse({'detail': _('ok'), 'name': project.name}, status=200)


receive_project = ReceiveProjectView.as_view()
