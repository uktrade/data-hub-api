from unittest.mock import Mock

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


def create_mock_search_app(
        current_mapping_hash='mapping-hash',
        target_mapping_hash='mapping-hash',
        read_indices=('test-index',),
        write_index='test-index',
        bulk_batch_size=1000,
        queryset=None,
):
    """Creates a mock search app."""
    return Mock(
        name='test-app',
        es_model=_create_mock_es_model(
            current_mapping_hash,
            target_mapping_hash,
            read_indices,
            write_index,
        ),
        bulk_batch_size=bulk_batch_size,
        queryset=queryset,
    )


def _create_mock_es_model(
        current_mapping_hash,
        target_mapping_hash,
        read_indices,
        write_index,
):
    def db_objects_to_es_documents(db_objects, index=None):
        for obj in db_objects:
            yield {
                '_index': index or write_index,
                '_id': getattr(obj, 'id'),
                '_type': 'test-type',
            }

    return Mock(
        __name__='es-model',
        create_index=Mock(),
        db_objects_to_es_documents=Mock(side_effect=db_objects_to_es_documents),
        get_current_mapping_hash=Mock(return_value=current_mapping_hash),
        get_target_mapping_hash=Mock(return_value=target_mapping_hash),
        get_read_and_write_indices=Mock(return_value=(set(read_indices), write_index)),
        get_write_index=Mock(return_value=write_index),
        get_read_alias=Mock(return_value='test-read-alias'),
        get_write_alias=Mock(return_value='test-write-alias'),
        get_target_index_name=Mock(return_value=f'test-index-{target_mapping_hash}'),
    )
