import collections

from django.utils import encoding

from datahub.interaction.models import ServiceDelivery
from datahub.v2.schemas.service_deliveries import ServiceDeliverySchema

DEFAULT = object()

_mapping = {
    ('company', 'Company'),
    ('contact', 'Contact'),
    ('country', 'Country'),
    ('dit_advisor', 'Advisor'),
    ('dit_team', 'Team'),
    ('sector', 'Sector'),
    ('service', 'Service'),
    ('status', 'ServiceDeliveryStatus'),
    ('uk_region', 'UKRegion')
}


mapping_attr_to_type = dict(_mapping)
mapping_type_to_attr = dict((v, k) for (k, v) in _mapping)


class RepoResponse:
    """Encapsulate the repo response.

    Data can be either a dictionary (detail view) or a list
    """

    def __init__(self, data, metadata=None, links=None):
        self.data = data
        self.metadata = metadata
        self.links = links


class ServiceDeliveryDatabaseRepo:
    """DB repo."""

    def __init__(self, config=None):
        """Initialise the repo using the config."""
        self.model_class = ServiceDelivery
        self.schema_class = ServiceDeliverySchema
        self.config = config
        self.url_builder = config['url_builder']

    def validate(self, data):
        """Validate the data against the schema."""
        self.schema_class().deserialize(data)

    def get(self, object_id):
        """Get and return a single object by its id."""
        entity = self.model_class.objects.get(id=object_id)
        data = model_to_json_api_data(entity, self.schema_class(), url_builder=self.url_builder)
        return build_repo_response(data=data)

    def filter(self, company_id=DEFAULT, contact_id=DEFAULT, offset=0, limit=100):
        """Filter objects."""
        filters = {}
        if company_id != DEFAULT:
            filters['company__pk'] = company_id
        if contact_id != DEFAULT:
            filters['contact__pk'] = contact_id
        start, end = offset, offset + limit
        entities = list(self.model_class.objects.filter(**filters).all()[start:end])
        data = [model_to_json_api_data(entity, self.schema_class(), self.url_builder) for entity in entities]
        return build_repo_response(data=data)

    def upsert(self, data):
        """Insert or update an object."""
        model_id = data.get('id', None)
        if model_id:
            data = merge_db_data_and_request_data(
                model_id,
                data,
                self.model_class,
                self.schema_class
            )
        self.validate(data)
        return json_api_to_model(data, self.model_class)


def model_to_json_api_data(model_instance, schema_instance, url_builder):
    """Convert the model instance to the JSON api format."""
    attributes = dict()
    relationships = dict()
    links = {'self': build_self_link(model_instance, url_builder)}
    for item in schema_instance:
        if item.name == 'attributes':
            for subitem in item:
                attributes[subitem.name] = build_attribute(model_instance, subitem.name)
        if item.name == 'relationships':
            for subitem in item:
                relationship_instance = getattr(model_instance, subitem.name, None)
                if relationship_instance:
                    relationships[subitem.name] = build_relationship(relationship_instance, subitem.name)
    return {
            'id': encoding.force_text(model_instance.pk),
            'type': model_instance.ENTITY_NAME,
            'attributes': attributes,
            'relationships': relationships,
            'links': links
        }


def build_relationship(model_instance, attribute):
    """Build relationships object from models."""
    entity_name = mapping_attr_to_type[attribute]
    data_dict = {'data': {'type': entity_name, 'id': str(model_instance.pk)}}
    return data_dict


def build_attribute(model_instance, attribute):
    """Build attributes object from model."""
    value = getattr(model_instance, attribute, None)
    if value:
        value = encoding.force_text(value)
    return value


def merge_db_data_and_request_data(model_id, data, model_class, schema_class):
    """If partial data is passed, we need to merge it with the existing data in the db."""
    object_from_db = model_class.objects.get(pk=model_id)
    object_from_db = model_to_json_api_data(object_from_db, schema_class())
    return dict_update_nested(object_from_db, data)


def dict_update_nested(dictionary, update):
    """Like update but for nested dictionary."""
    for k, v in update.items():
        if isinstance(v, collections.Mapping):
            r = dict_update_nested(dictionary.get(k, {}), v)
            dictionary[k] = r
        else:
            dictionary[k] = update[k]
    return dictionary


def build_repo_response(data):
    """Enriched repo response, containing data, metadata and links."""
    return RepoResponse(
        data=data,
        metadata=build_meta(),
        links=build_links()
    )


def build_self_link(model_instance, url_builder):
    """Build self link for an entity, give a url builder function."""
    object_id = encoding.force_text(model_instance.pk)
    return url_builder(kwargs={'object_id': object_id})


def json_api_to_model(data, model_class):
    """Take JSON api format data and tries to save or update a model instance."""
    model_attrs = data.get('attributes', {})
    model_id = data.pop('id', None)
    for key, value in data.get('relationships', {}).items():
        model_attrs[key + '_id'] = value['data']['id']
    if model_id:
        return update_model(model_class, model_attrs, model_id)
    else:
        return model_class.objects.create(**model_attrs)


def update_model(model_class, model_attrs, object_id):
    """Update an existing model."""
    obj = model_class.objects.get(pk=object_id)
    for key, value in model_attrs.items():
        setattr(obj, key, value)
    obj.save()
    return obj


def build_meta():
    """Metadata to be shown in the list view."""
    return {
        'pagination': {
            'count': None,
            'limit': None,
            'offset': None
        }
    }


def build_links():
    """Pagination links to be"""
    return {
        'first': '',
        'last': '',
        'next': '',
        'prev': ''
    }
