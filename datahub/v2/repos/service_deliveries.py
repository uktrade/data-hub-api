import datetime

from datahub.interaction.models import ServiceDelivery
from datahub.v2.serializers.service_deliveries import ServiceDeliverySchema

DEFAULT = object()

_mapping = {
    ('company', 'Company'),
    ('contact', 'Contact'),
    ('country', 'Country'),
    ('dit_advisor', 'Advisor'),
    ('dit_team', 'Team'),
    ('sector', 'Sector'),
    ('service', 'Service'),
    ('status', 'Status'),
    ('uk_region', 'UKRegion')
}


mapping_attr_to_type = dict(_mapping)
mapping_type_to_attr = dict((v, k) for (k, v) in _mapping)


class ServiceDeliveryDatabaseRepo:
    """DB repo."""

    def __init__(self, config=None):
        """Initialise the repo using the config."""
        self.model = ServiceDelivery
        self.schema = ServiceDeliverySchema

    def get(self, object_id):
        """Get and return a single object by its id."""
        model_instance = self.model.objects.get(id=object_id)
        return model_to_json_api(model_instance, schema_instance=self.schema())

    def filter(self, company_id=DEFAULT, contact_id=DEFAULT, offset=0, limit=100):
        """Filter objects."""
        queryset = self.model.objects
        if company_id:
            queryset.filter(company__pk=company_id)
        if contact_id:
            queryset.filter(contact__pk=contact_id)
        return [model_to_json_api(item, self.schema()) for item in queryset.all()]

    def upsert(self, data):
        """Insert or update an object."""
        return json_api_to_model(data, model_class=self.model)


def build_relationship(model_instance, attribute):
    entity_name = mapping_attr_to_type[attribute]
    data_dict = {'data': {'type': entity_name, 'id': str(model_instance.pk)}}
    return data_dict


def build_attribute(model_instance, attribute):
    value = getattr(model_instance, attribute, None)
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    else:
        return value


def model_to_json_api(model_instance, schema_instance):
    attributes = dict()
    relationships = dict()
    for item in schema_instance:
        if item.name == 'attributes':
            for subitem in item:
                attributes[subitem.name] = build_attribute(model_instance, subitem.name)
        elif item.name == 'relationships':
            for subitem in item:
                relationship_instance = getattr(model_instance, subitem.name, None)
                if relationship_instance:
                    relationships[subitem.name] = build_relationship(relationship_instance, subitem.name)
    return {'attributes': attributes, 'relationships': relationships}


def json_api_to_model(data, model_class):
    model_attrs = data.get('attributes', {})
    for key, value in data.get('relationships', {}).items():
        model_attrs[key + '_id'] = value['data']['id']
    return model_class(**model_attrs)
