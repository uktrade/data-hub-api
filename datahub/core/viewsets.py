from django.core.exceptions import ValidationError
from rest_framework import mixins
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.viewsets import GenericViewSet


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
        if self.action in ('list', 'retrieve', 'archive'):
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


CoreViewSetV3 = CoreViewSetV1
