import collections
import datetime
import uuid

import colander
from django.utils import encoding


DEFAULT = object()


class RepoResponse:
    """Encapsulate the repo response.

    Data can be either a dictionary (detail view) or a list
    """

    def __init__(self, data, metadata=None, links=None, status=None):
        """Set data, metadata and links."""
        self.data = data
        self.metadata = metadata
        self.links = links
        self.status = status


def model_to_json_api_data(model_instance, schema_instance, url_builder):
    """Convert the model instance to the JSON api format."""
    attributes = dict()
    relationships = dict()
    links = {'self': build_self_link(model_instance, url_builder)}
    attribute_to_type_mapping = attributes_to_types(model_instance.API_MAPPING)
    for item in schema_instance:
        if item.name == 'attributes':
            for subitem in item:
                attributes[subitem.name] = build_attribute(model_instance, subitem.name)
        if item.name == 'relationships':
            for subitem in item:
                relationship_instance = getattr(model_instance, subitem.name)
                if relationship_instance:
                    relationships[subitem.name] = build_relationship(
                        relationship_instance,
                        subitem.name,
                        attribute_to_type_mapping
                    )
    return {
        'id': encoding.force_text(model_instance.pk),
        'type': model_instance.ENTITY_NAME,
        'attributes': attributes,
        'relationships': relationships,
        'links': links
    }


def attributes_to_types(mapping):
    """Take a dictionary of tuples.

    {('foo', 'Foo'), ('bar', 'Bar')}

    return a dictionary

    {'foo': 'Foo', 'bar': 'Bar'}
    """
    return dict(mapping)


def build_relationship(model_instance, attribute, attribute_to_type_mapping):
    """Build relationships object from models."""
    entity_name = attribute_to_type_mapping[attribute]
    data_dict = {'data': {'type': entity_name, 'id': encoding.force_text(model_instance.pk)}}
    return data_dict


def build_attribute(model_instance, attribute):
    """Build attributes object from model."""
    value = getattr(model_instance, attribute)
    if isinstance(value, uuid.UUID):
        return encoding.force_text(value)
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    return value


def merge_db_data_and_request_data(model_id, data, model_class, schema_class, url_builder):
    """If partial data is passed, we need to merge it with the existing data in the db."""
    object_from_db = model_class.objects.get(pk=model_id)
    object_from_db = model_to_json_api_data(object_from_db, schema_class(), url_builder)
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


def build_repo_response(data, status=None):
    """Enriched repo response, containing data, metadata and links."""
    return RepoResponse(
        data=data,
        metadata=build_meta(),
        links=build_links(),
        status=status
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
        try:
            model_attrs[key + '_id'] = value['data']['id']
        except TypeError:
            model_attrs[key + '_id'] = None
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
    """Metadata to be shown in the list view.

    Not in use yet.
    """
    return {
        'pagination': {
            'count': None,
            'limit': None,
            'offset': None
        }
    }


def build_links():
    """Pagination links to be populated in the future."""
    return {
        'first': '',
        'last': '',
        'next': '',
        'prev': ''
    }


def extract_id_for_relationship_from_data(data, relationship_name):
    """Give JSON api formatted data and a relationship name return the ID."""
    relationship_data = data.get('relationships', {}).get(relationship_name, {})
    if relationship_data:
        return relationship_data.get('data', {}).get('id')


def replace_colander_null(data):
    """Replace colander.null with None in deserialized data."""
    cleaned_data = {
        'attributes': {k: None if v is colander.null else v for k, v in data['attributes'].items()},
        'relationships': {k: None if v is colander.null else v for k, v in data['relationships'].items()}
    }
    data.update(cleaned_data)
    return data
