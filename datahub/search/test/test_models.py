import inspect

from django.utils.functional import cached_property

from datahub.search.apps import get_search_apps


def pytest_generate_tests(metafunc):
    """Parametrizes the tests that use the `search_app` fixture."""
    if 'search_app' in metafunc.fixturenames:
        apps = get_search_apps()
        metafunc.parametrize(
            'search_app',
            apps,
            ids=[app.__class__.__name__ for app in apps]
        )


def test_validate_model_fields(search_app):
    """Test that all top-level fields defined in search models are valid."""
    es_model = search_app.es_model
    db_model = search_app.queryset.model

    fields = _get_es_model_fields(es_model)

    copy_to_fields = _get_es_model_copy_to_fields(es_model)
    computed_fields = es_model.COMPUTED_MAPPINGS.keys()
    db_model_properties = _get_object_properties(db_model)
    db_model_fields = _get_db_model_fields(db_model)

    valid_fields = copy_to_fields | computed_fields | db_model_properties | db_model_fields
    invalid_fields = fields - valid_fields

    assert not invalid_fields


def test_validate_model_mapping_fields(search_app):
    """Test that all fields defined in MAPPINGS exist on the ES model."""
    es_model = search_app.es_model
    valid_fields = _get_es_model_fields(es_model)
    fields = es_model.MAPPINGS.keys()
    invalid_fields = fields - valid_fields

    assert not invalid_fields


def _get_es_model_es_properties(es_model):
    return es_model._doc_type.mapping.properties._params['properties']


def _get_es_model_fields(es_model):
    return _get_es_model_es_properties(es_model).keys()


def _get_es_model_copy_to_fields(es_model):
    props = _get_es_model_es_properties(es_model)

    copy_to_field_lists = [
        [prop.copy_to] if isinstance(prop.copy_to, str) else prop.copy_to
        for prop in props.values()
        if hasattr(prop, 'copy_to')
    ]

    return {field for fields in copy_to_field_lists for field in fields}


def _get_db_model_fields(db_model):
    return {field.name for field in db_model._meta.get_fields()}


def _get_object_properties(obj):
    return {prop[0] for prop in inspect.getmembers(obj, _is_property)}


def _is_property(obj):
    return isinstance(obj, (property, cached_property))
