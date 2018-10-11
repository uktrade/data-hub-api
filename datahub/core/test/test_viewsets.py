from django.contrib.auth import get_user_model
from rest_framework import serializers, status
from rest_framework.test import APIRequestFactory, force_authenticate

from datahub.core.test.support.models import EmptyModel, InheritedModel
from datahub.core.test_utils import APITestMixin
from datahub.core.viewsets import CoreViewSet

factory = APIRequestFactory()


class InheritedModelSerializer(serializers.ModelSerializer):
    """DRF Serializer to use with the InheritedModel."""

    class Meta:
        model = InheritedModel
        depth = 1
        fields = '__all__'


class EmptyModelSerializer(serializers.ModelSerializer):
    """DRF Serializer to use with the EmptyModel."""

    class Meta:
        model = EmptyModel
        depth = 1
        fields = '__all__'


class InheritedModelViewSet(CoreViewSet):
    """DRF ViewSet to use with the InheritedModel."""

    permission_classes = []
    queryset = InheritedModel.objects.all()
    serializer_class = InheritedModelSerializer


class EmptyModelViewSet(CoreViewSet):
    """DRF ViewSet to use with the EmptyModel."""

    permission_classes = []
    queryset = EmptyModel.objects.all()
    serializer_class = EmptyModelSerializer


class TestCoreViewSet(APITestMixin):
    """Tests for CoreViewSet"""

    def test_create_populates_created_modified_by_if_they_exist(self):
        """
        Tests that if the view extends CoreViewSet and the model
        has created_by and modified_by, they will be set during the creation.
        """
        request = factory.post('/', data={}, content_type='application/json')
        force_authenticate(request, self.user)

        my_view = InheritedModelViewSet.as_view(
            actions={'post': 'create'},
        )

        response = my_view(request)
        assert response.status_code == status.HTTP_201_CREATED

        created_instance = InheritedModel.objects.first()
        assert created_instance.created_by == self.user
        assert created_instance.modified_by == self.user

    def test_update_updates_modified_by_if_it_exists(self):
        """
        Tests that if the view extends CoreViewSet and the model
        has modified_by, it will be updated when updating.
        """
        # prepare test
        other_user = get_user_model().objects.create()
        inherited_model = InheritedModel.objects.create(
            created_by=other_user,
            modified_by=other_user,
        )

        # create response
        request = factory.patch('/', data={}, content_type='application/json')
        force_authenticate(request, self.user)

        my_view = InheritedModelViewSet.as_view(
            actions={'patch': 'partial_update'},
        )

        response = my_view(request, pk=inherited_model.pk)
        assert response.status_code == status.HTTP_200_OK

        # check
        inherited_model.refresh_from_db()
        assert inherited_model.created_by == other_user
        assert inherited_model.modified_by == self.user

    def test_create_doesnt_populate_created_modified_by_if_they_dont_exist(self):
        """
        Tests that if the view extends CoreViewSet but the model
        doesn't have created_by and modified_by, they won't be set during the creation.
        """
        request = factory.post('/', data={}, content_type='application/json')
        force_authenticate(request, self.user)

        my_view = EmptyModelViewSet.as_view(
            actions={'post': 'create'},
        )

        response = my_view(request)
        assert response.status_code == status.HTTP_201_CREATED

        created_instance = EmptyModel.objects.first()
        assert not hasattr(created_instance, 'created_by')
        assert not hasattr(created_instance, 'modified_by')

    def test_update_doesnt_update_modified_by_if_it_doesnt_exists(self):
        """
        Tests that if the view extends CoreViewSet but the model
        doesn't have modified_by, it won't be updated when updating.
        """
        # prepare test
        empty_model = EmptyModel.objects.create()

        # create response
        request = factory.patch('/', data={}, content_type='application/json')
        force_authenticate(request, self.user)

        my_view = EmptyModelViewSet.as_view(
            actions={'patch': 'partial_update'},
        )

        response = my_view(request, pk=empty_model.pk)
        assert response.status_code == status.HTTP_200_OK

        # check
        empty_model.refresh_from_db()
        assert not hasattr(empty_model, 'created_by')
        assert not hasattr(empty_model, 'modified_by')
