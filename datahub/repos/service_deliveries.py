from datahub.interaction.serializers import ServiceDeliverySerializerV2
from datahub.interaction.models import ServiceDelivery


DEFAULT = object()


class ServiceDeliveryDatabaseRepo:
    """DB repo."""

    def __init__(self, config=None):
        """Initialise the repo using the config."""
        self.model = ServiceDelivery
        self.serializer = ServiceDeliverySerializerV2

    def get(self, object_id):
        """Get and return a single object by its id."""
        try:
            return self.serializer(self.model.objects.get(id=object_id)).data
        except self.model.DoesNotExist:
            return {}

    def filter(self, company_id=DEFAULT, contact_id=DEFAULT):
        """Filter objects."""
        queryset = self.model.objects
        if company_id:
            queryset.filter(company__pk=company_id)
        if contact_id:
            queryset.filter(contact__pk=contact_id)
        return self.serializer(queryset.all(), many=True).data

    def upsert(self, data):
        """Insert or update an object."""
        obj_id = data.pop('id')
        obj, _ = self.model.objects.update_or_create(
            pk=obj_id,
            defaults=data
        )
        return self.serializer(obj).data


class ServiceDeliveryJSONRepo:
    """Json based repo."""

    def __init__(self, config=None):
        self.folder = config['source']

    def get(self, object_id):
        pass

    def filter(self, company_id=DEFAULT, contact_id=DEFAULT):
        pass
