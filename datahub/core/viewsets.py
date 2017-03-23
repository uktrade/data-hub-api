from django.core.exceptions import ValidationError
from django.db import transaction
from raven.contrib.django.raven_compat.models import client
from rest_framework import mixins
from rest_framework import parsers
from rest_framework.exceptions import APIException
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.viewsets import GenericViewSet, ViewSet
from rest_framework_json_api import pagination as json_api_pagination
from rest_framework_json_api import parsers as json_api_parsers
from rest_framework_json_api import renderers as json_api_renderers
from rest_framework_json_api.metadata import JSONAPIMetadata

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

    @staticmethod
    def _handle_model_validation_error(exception, version):
        """Return different validation format based on version."""
        if version and version == 'v2':
            raise DRFValidationError(detail=exception.message_dict)
        raise DRFValidationError({'errors': exception.message_dict})

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
            self._handle_model_validation_error(e, request.version)
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
            self._handle_model_validation_error(e, request.version)
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


class CoreViewSetV2(ViewSet):
    """JSON API V2 views."""

    pagination_class = json_api_pagination.LimitOffsetPagination
    parser_classes = (json_api_parsers.JSONParser, parsers.FormParser, parsers.MultiPartParser)
    renderer_classes = (json_api_renderers.JSONRenderer, BrowsableAPIRenderer)
    metadata_class = JSONAPIMetadata
    repo_class = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.repo_class, 'A repo class needs to be defined.'

    def list(self, request, *args, **kwargs):
        pass

    def retrieve(self, request, *args, **kwargs):
        pass

    def create(self, request, *args, **kwargs):
        pass

    def update(self, request, pk=None):
        pass

    def partial_update(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        pass
