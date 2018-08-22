from openwisp_utils.api.serializers import ValidatedModelSerializer
from test_project.models import Shelf


class ShelfSerializer(ValidatedModelSerializer):
    class Meta:
        model = Shelf
        fields = '__all__'
