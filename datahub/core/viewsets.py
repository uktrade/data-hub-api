from django.core.exceptions import FieldDoesNotExist, ValidationError
from rest_framework import mixins
from rest_framework.exceptions import ValidationError as DRFValidationError
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


class CoreViewSetV1(mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.ListModelMixin,
                    GenericViewSet):
    """Handle custom validation errors in a DRF friendly way."""

    read_serializer_class = None
    write_serializer_class = None

    def get_serializer_class(self):
        """Return a different serializer class for reading or writing, if defined."""
        if self.action in ('list', 'retrieve', 'archive', 'unarchive'):
            return self.read_serializer_class
        elif self.action in ('create', 'update', 'partial_update'):
            return self.write_serializer_class

    def create(self, request, *args, **kwargs):
        """Override create to catch the validation errors coming from the models.

        These are not real Exceptions, rather user errors.
        """
        try:
            return super().create(request, *args, **kwargs)
        except ValidationError as e:
            raise DRFValidationError({'errors': e.message_dict})

    def update(self, request, *args, **kwargs):
        """Override update to catch the validation errors coming from the models.

        These are not real Exceptions, rather user errors.
        """
        try:
            return super().update(request, *args, **kwargs)
        except ValidationError as e:
            raise DRFValidationError({'errors': e.message_dict})

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


class CoreViewSetV3(mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    mixins.ListModelMixin,
                    GenericViewSet):
    """Base class for v3 view sets."""

    def perform_create(self, serializer):
        """Custom logic for creating the model instance.

        At the moment some models are raising Django validation errors;
        these are converted to DRF validation errors so a proper error
        response is generated.
        """
        extra_data = self.get_additional_data(True)
        try:
            serializer.save(**extra_data)
        except ValidationError as e:
            raise DRFValidationError(e.message_dict)

    def perform_update(self, serializer):
        """Custom logic for updating the model instance.

        At the moment some models are raising Django validation errors;
        these are converted to DRF validation errors so a proper error
        response is generated.
        """
        extra_data = self.get_additional_data(False)
        try:
            serializer.save(**extra_data)
        except ValidationError as e:
            raise DRFValidationError(e.message_dict)

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
