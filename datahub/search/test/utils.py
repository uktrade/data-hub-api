from elasticsearch_dsl import AttrDict

from datahub.search.utils import get_model_fields


def model_has_field_path(es_model, path):
    """Checks whether a field path (e.g. company.id) exists in a model."""
    path_components = path.split('.')
    fields = get_model_fields(es_model)

    for sub_field_name in path_components:
        if sub_field_name not in fields:
            return False

        sub_field = fields.get(sub_field_name)
        fields = getattr(sub_field, 'properties', AttrDict({})).to_dict()
        if not fields:
            fields = getattr(sub_field, 'fields', {})

    return True
