from django.core.exceptions import ValidationError
from django.db import transaction
from raven.contrib.django.raven_compat.models import client
from rest_framework import mixins
from rest_framework.exceptions import APIException
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.viewsets import GenericViewSet

from datahub.company import tasks
from datahub.korben.exceptions import KorbenException


class CoreViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.ListModelMixin,
                  GenericViewSet):
    """Save to korben hook."""

    def _save_to_korben(self, object_id, user_id, update):
        """Spawn the task to save to Korben."""
        model_class = self.get_serializer_class().Meta.model
        obj = model_class.objects.get(pk=object_id)
        tasks.save_to_korben.delay(
            data=obj.convert_model_to_korben_format(),
            user_id=user_id,
            db_table=model_class._meta.db_table,
            update=update
        )

    def create(self, request, *args, **kwargs):
        """Override create to catch the validation errors coming from the models.

        These are not real Exceptions, rather user errors.
        """
        try:

            with transaction.atomic():
                response = super().create(request, *args, **kwargs)
            self._save_to_korben(
                object_id=response.data['id'],
                user_id=request.user.id,
                update=False
            )
            return response
        except ValidationError as e:
            raise DRFValidationError({'errors': e.message_dict})
        except KorbenException as e:
            raise APIException(detail=e.message)

    def update(self, request, *args, **kwargs):
        """Override update to catch the validation errors coming from the models.

        These are not real Exceptions, rather user errors.
        """
        try:
            with transaction.atomic():
                response = super().update(request, *args, **kwargs)
            self._save_to_korben(
                object_id=response.data['id'],
                user_id=request.user.id,
                update=True
            )
            return response
        except ValidationError as e:
            raise DRFValidationError({'errors': e.message_dict})
        except KorbenException as e:
            raise APIException(detail=e.message)

    def retrieve(self, request, *args, **kwargs):
        """Override to handle the exceptions coming from Korben."""
        try:
            return super().retrieve(request, *args, **kwargs)
        except KorbenException:
            client.captureException()
            raise APIException(detail='Korben error.')


class CoreViewSetV1(CoreViewSet):
    """Implement the read/write serializers."""

    read_serializer_class = None
    write_serializer_class = None

    def get_serializer_class(self):
        """Return a different serializer class for reading or writing, if defined."""
        if self.action in ('list', 'retrieve', 'archive'):
            return self.read_serializer_class
        elif self.action in ('create', 'update', 'partial_update'):
            return self.write_serializer_class
