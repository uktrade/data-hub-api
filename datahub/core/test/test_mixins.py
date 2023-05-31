from rest_framework import serializers, status
from rest_framework.test import APIRequestFactory, force_authenticate

from datahub.core.test.support.models import EmptyModel
from datahub.core.test_utils import APITestMixin
from datahub.core.viewsets import SoftDeleteCoreViewSet

factory = APIRequestFactory()
AUTH_USER_MODEL = 'company.Advisor'


class TestEmptyModelSerializer(serializers.ModelSerializer):
    """DRF Serializer to use with the EmptyModel."""

    class Meta:
        model = EmptyModel
        depth = 1
        fields = '__all__'


class TestEmptyModelSoftDeleteCoreViewSet(SoftDeleteCoreViewSet):
    lookup_field = 'id'
    permission_classes = []
    queryset = EmptyModel.objects.all()
    serializer_class = TestEmptyModelSerializer


class TestSoftDeleteViaArchiveMixin(APITestMixin):
    def test_destroy_with_non_archivable_model_deletes_object(self):

        empty_model = EmptyModel.objects.create()
        id = empty_model.id

        my_view = TestEmptyModelSoftDeleteCoreViewSet.as_view(
            {
                'delete': 'destroy',
                'get': 'retrieve',
            },
        )

        delete_request = factory.delete(f'/{id}/')
        force_authenticate(delete_request, self.user)

        delete_response = my_view(delete_request, id=id)
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        get_request = factory.get(f'/{id}/')
        force_authenticate(get_request, self.user)

        get_response = my_view(get_request, id=id)

        assert get_response.status_code == status.HTTP_404_NOT_FOUND
