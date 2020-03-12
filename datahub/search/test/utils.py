from unittest.mock import Mock


def create_mock_search_app(
        current_mapping_hash='mapping-hash',
        target_mapping_hash='mapping-hash',
        read_indices=('test-index',),
        write_index='test-index',
        bulk_batch_size=1000,
        queryset=None,
):
    """Creates a mock search app."""
    mock = Mock()
    mock.configure_mock(
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
    return mock


def doc_exists(es_client, search_app, id_):
    """Checks if a document exists for a specified search app."""
    return es_client.exists(
        index=search_app.es_model.get_read_alias(),
        doc_type=search_app.name,
        id=id_,
    )


def doc_count(es_client, search_app):
    """Return a document count for a specified search app."""
    response = es_client.count(
        index=search_app.es_model.get_read_alias(),
        doc_type=search_app.name,
    )
    return response['count']


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
                '_id': obj.id,
                '_type': 'test-type',
            }

    return Mock(
        __name__='es-model',
        create_index=Mock(),
        db_objects_to_es_documents=Mock(side_effect=db_objects_to_es_documents),
        is_migration_needed=Mock(return_value=current_mapping_hash != target_mapping_hash),
        was_migration_started=Mock(return_value=len(read_indices) > 1),
        get_current_mapping_hash=Mock(return_value=current_mapping_hash),
        get_target_mapping_hash=Mock(return_value=target_mapping_hash),
        get_read_and_write_indices=Mock(return_value=(set(read_indices), write_index)),
        get_write_index=Mock(return_value=write_index),
        get_read_alias=Mock(return_value='test-read-alias'),
        get_write_alias=Mock(return_value='test-write-alias'),
        get_target_index_name=Mock(return_value=f'test-index-{target_mapping_hash}'),
        set_up_index_and_aliases=Mock(return_value=False),
    )


def get_documents_by_ids(es_client, app, ids):
    """Get given search app documents by supplied ids."""
    return es_client.mget(
        index=app.es_model.get_read_alias(),
        doc_type=app.name,
        body={
            'ids': ids,
        },
    )
