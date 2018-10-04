from django.core.exceptions import FieldDoesNotExist
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet


def has_fields(model, *fields):
    """Returns True if model has all the fields, False otherwise."""
    meta = model._meta

    try:
        for field in fields:
            meta.get_field(field)
    except FieldDoesNotExist:
        return False
    return True


class CoreViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """Base class for view sets."""

    def perform_create(self, serializer):
        """Custom logic for creating the model instance."""
        extra_data = self.get_additional_data(True)
        serializer.save(**extra_data)

    def perform_update(self, serializer):
        """Custom logic for updating the model instance."""
        extra_data = self.get_additional_data(False)
        serializer.save(**extra_data)

    def get_additional_data(self, create):
        """Returns additional data to be saved in the model instance.

        Intended to be overridden by subclasses.

        :param create:  True for is a model instance is being created; False
                        for updates
        :return:        dict of additional data to be saved
        """
        additional_data = {}
        if has_fields(self.get_queryset().model, 'created_by', 'modified_by'):
            additional_data['modified_by'] = self.request.user

            if create:
                additional_data['created_by'] = self.request.user

        return additional_data
