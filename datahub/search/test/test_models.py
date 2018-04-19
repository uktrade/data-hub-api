import inspect

from django.utils.functional import cached_property

from datahub.search.utils import get_model_copy_to_target_field_names, get_model_field_names


def test_validate_model_fields(search_app):
    """Test that all top-level fields defined in search models are valid."""
    es_model = search_app.es_model
    db_model = search_app.queryset.model

    fields = get_model_field_names(es_model)

    copy_to_fields = get_model_copy_to_target_field_names(es_model)
    computed_fields = es_model.COMPUTED_MAPPINGS.keys()
    db_model_properties = _get_object_properties(db_model)
    db_model_fields = _get_db_model_fields(db_model)

    valid_fields = copy_to_fields | computed_fields | db_model_properties | db_model_fields
    invalid_fields = fields - valid_fields

    assert not invalid_fields


def test_validate_model_mapping_fields(search_app):
    """Test that all fields defined in MAPPINGS exist on the ES model."""
    es_model = search_app.es_model
    valid_fields = get_model_field_names(es_model)
    fields = es_model.MAPPINGS.keys()
    invalid_fields = fields - valid_fields

    assert not invalid_fields


def test_validate_model_computed_mapping_fields(search_app):
    """Test that all fields defined in COMPUTED_MAPPINGS exist on the ES model."""
    es_model = search_app.es_model
    valid_fields = get_model_field_names(es_model)
    fields = es_model.COMPUTED_MAPPINGS.keys()
    invalid_fields = fields - valid_fields

    assert not invalid_fields


def test_validate_model_no_mapping_and_computed_intersection(search_app):
    """Test that MAPPINGS and COMPUTED_MAPPINGS on ES models don't overlap."""
    es_model = search_app.es_model
    intersection = es_model.MAPPINGS.keys() & es_model.COMPUTED_MAPPINGS.keys()

    assert not intersection


def _get_db_model_fields(db_model):
    return {field.name for field in db_model._meta.get_fields()}


def _get_object_properties(obj):
    return {prop[0] for prop in inspect.getmembers(obj, _is_property)}


def _is_property(obj):
    return isinstance(obj, (property, cached_property))
