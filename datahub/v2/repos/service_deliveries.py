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

    def filter(self, company_id=DEFAULT, contact_id=DEFAULT, offset=0, limit=100):
        """Filter objects."""
        queryset = self.model.objects
        if company_id:
            queryset.filter(company__pk=company_id)
        if contact_id:
            queryset.filter(contact__pk=contact_id)
        return self.serializer(queryset.all(), many=True).data

    def upsert(self, data, user):
        """Insert or update an object."""
        obj_id = data.pop('id')
        obj, _ = self.model.objects.update_or_create(
            pk=obj_id,
            defaults=data
        )
        return self.serializer(obj).data
