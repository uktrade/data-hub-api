import inspect

import pytest
from django.utils.functional import cached_property

from datahub.search.test.search_support.models import SimpleModel
from datahub.search.test.search_support.simplemodel.models import SearchSimpleModel
from datahub.search.utils import get_model_field_names


class TestBaseSearchModel:
    """Tests for BaseSearchModel."""

    @pytest.mark.parametrize('include_index', (False, True))
    @pytest.mark.parametrize('include_source', (False, True))
    def test_to_document(self, include_index, include_source):
        """Test that to_document() creates a dict with the expected keys and values."""
        obj = SimpleModel(id=5, name='test-name', address='123 Fake Street', country='uk')
        doc = SearchSimpleModel.to_document(
            obj,
            include_index=include_index,
            include_source=include_source,
        )
        source = {
            '_document_type': 'simplemodel',
            'id': obj.pk,
            'name': 'test-name',
            'address': '123 Fake Street',
            'country': 'uk',
            'date': None,
            'archived': False,
        }

        expected_doc = {
            '_id': obj.pk,
            **({'_index': SearchSimpleModel.get_write_alias()} if include_index else {}),
            **({'_source': source} if include_source else {}),
        }

        assert doc == expected_doc


def test_validate_model_fields(search_app):
    """Test that all top-level fields defined in search models are valid."""
    search_model = search_app.search_model
    db_model = search_app.queryset.model

    fields = get_model_field_names(search_model)

    computed_fields = search_model.COMPUTED_MAPPINGS.keys()
    db_model_properties = _get_object_properties(db_model)
    db_model_fields = _get_db_model_fields(db_model)

    valid_fields = computed_fields | db_model_properties | db_model_fields | {'_document_type'}
    invalid_fields = fields - valid_fields

    assert not invalid_fields


def test_validate_model_mapping_fields(search_app):
    """Test that all fields defined in MAPPINGS exist on the OpenSearch model."""
    search_model = search_app.search_model
    valid_fields = get_model_field_names(search_model)
    fields = search_model.MAPPINGS.keys()
    invalid_fields = fields - valid_fields

    assert not invalid_fields


def test_validate_model_computed_mapping_fields(search_app):
    """Test that all fields defined in COMPUTED_MAPPINGS exist on the OpenSearch model."""
    search_model = search_app.search_model
    valid_fields = get_model_field_names(search_model)
    fields = search_model.COMPUTED_MAPPINGS.keys()
    invalid_fields = fields - valid_fields

    assert not invalid_fields


def test_validate_model_no_mapping_and_computed_intersection(search_app):
    """Test that MAPPINGS and COMPUTED_MAPPINGS on OpenSearch models don't overlap."""
    search_model = search_app.search_model
    intersection = search_model.MAPPINGS.keys() & search_model.COMPUTED_MAPPINGS.keys()

    assert not intersection


def test_validate_model_search_fields(search_app):
    """Test that all field paths in SEARCH_FIELDS exist on the OpenSearch model."""
    search_model = search_app.search_model
    mapping = search_model._doc_type.mapping
    invalid_fields = {
        field for field in search_model.SEARCH_FIELDS if not mapping.resolve_field(field)
    }

    assert (
        not invalid_fields
    ), f'Invalid search fields {invalid_fields} detected on {search_model.__name__} search model'


def _get_db_model_fields(db_model):
    return {field.name for field in db_model._meta.get_fields()}


def _get_object_properties(obj):
    return {prop[0] for prop in inspect.getmembers(obj, _is_property)}


def _is_property(obj):
    return isinstance(obj, (property, cached_property))
