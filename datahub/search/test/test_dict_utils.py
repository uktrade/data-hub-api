from unittest import mock

import pytest
from pytest import raises

from datahub.search import dict_utils


def _construct_mock(**props):
    """
    Same as mock.Mock() but using configure_mock as
    name collides with the kwarg in the Mock constructor.
    """
    obj = mock.Mock(spec_set=tuple(props.keys()))
    obj.configure_mock(**props)
    return obj


def test_id_name_dict():
    """Tests _id_name_dict."""
    obj = mock.Mock()
    obj.id = 123
    obj.name = 'test'

    res = dict_utils.id_name_dict(obj)

    assert res == {
        'id': str(obj.id),
        'name': obj.name,
    }


def test_id_name_list_of_dicts():
    """Test that id_name_list_of_dicts returns a list of dicts with ID and name keys."""
    data = [
        {'id': '12', 'name': 'test A'},
        {'id': '99', 'name': 'testing B'},
    ]
    objects = [mock.Mock(), mock.Mock()]
    for obj, data_item in zip(objects, data):
        obj.configure_mock(**data_item)

    manager = mock.Mock(
        all=mock.Mock(return_value=objects),
    )

    assert dict_utils.id_name_list_of_dicts(manager) == data


def test_id_type_dict():
    """Tests _id_type_dict."""
    obj = mock.Mock()
    obj.id = 123
    obj.type = 'test'

    res = dict_utils.id_type_dict(obj)

    assert res == {
        'id': str(obj.id),
        'type': obj.type,
    }


def test_id_uri_dict():
    """Tests _id_type_dict."""
    obj = mock.Mock()
    obj.id = 123
    obj.uri = 'test'

    res = dict_utils.id_uri_dict(obj)

    assert res == {
        'id': str(obj.id),
        'uri': obj.uri,
    }


class TestCompanyDict:
    """Tests for the company_dict function."""

    def test_complete(self):
        """Test with all fields filled in."""
        obj = mock.Mock(
            id=123,
            name='Name',
            trading_names=['Trading 1', 'Trading 2'],
            spec_set=('id', 'name', 'trading_names'),
        )

        res = dict_utils.company_dict(obj)

        assert res == {
            'id': str(obj.id),
            'name': obj.name,
            'trading_name': obj.trading_names[0],
            'trading_names': obj.trading_names,
        }

    def test_minimal(self):
        """Test with only minimal fields filled in."""
        obj = mock.Mock(
            id=123,
            name='Name',
            trading_names=[],
            spec_set=('id', 'name', 'trading_names'),
        )

        res = dict_utils.company_dict(obj)

        assert res == {
            'id': str(obj.id),
            'name': obj.name,
            'trading_name': '',
            'trading_names': [],
        }

    def test_none(self):
        """Test that if company is None, the resulting dict is None."""
        res = dict_utils.company_dict(None)

        assert res is None


@pytest.mark.parametrize(
    'obj,fields_prefix,expected_address_dict',
    (
        # returns None in case of empty address fields values
        (
            _construct_mock(
                address_1='',
                address_2='',
                address_town='',
                address_county='',
                address_postcode='',
                address_country=None,
            ),
            'address',
            None,
        ),

        # returns None when obj is None
        (
            None,
            'address',
            None,
        ),

        # all fields converted into a dict
        (
            _construct_mock(
                primary_address_1='1',
                primary_address_2='Main Road',
                primary_address_town='London',
                primary_address_county='Greenwich',
                primary_address_postcode='SE10 9NN',
                primary_address_country=_construct_mock(
                    id='80756b9a-5d95-e211-a939-e4115bead28a',
                    name='United Kingdom',
                ),
            ),
            'primary_address',
            {
                'line_1': '1',
                'line_2': 'Main Road',
                'town': 'London',
                'county': 'Greenwich',
                'postcode': 'SE10 9NN',
                'country': {
                    'id': '80756b9a-5d95-e211-a939-e4115bead28a',
                    'name': 'United Kingdom',
                },
            },
        ),


        # None values converted to ''
        (
            _construct_mock(
                primary_address_1=None,
                primary_address_2=None,
                primary_address_town=None,
                primary_address_county=None,
                primary_address_postcode=None,
                primary_address_country=_construct_mock(
                    id='80756b9a-5d95-e211-a939-e4115bead28a',
                    name='United Kingdom',
                ),
            ),
            'primary_address',
            {
                'line_1': '',
                'line_2': '',
                'town': '',
                'county': '',
                'postcode': '',
                'country': {
                    'id': '80756b9a-5d95-e211-a939-e4115bead28a',
                    'name': 'United Kingdom',
                },
            },
        ),
    ),
)
def test_address_dict(obj, fields_prefix, expected_address_dict):
    """Tests for address_dict."""
    address = dict_utils.address_dict(obj, prefix=fields_prefix)

    assert address == expected_address_dict


def test_address_dict_raises_error_with_invalid_prefix():
    """
    Tests that if address_dict is called with a prefix that
    cannot be found on the object, an AttributeError is raised.
    """
    obj = _construct_mock(
        primary_address_1='1',
        primary_address_2='Main Road',
        primary_address_town='London',
        primary_address_county='Greenwich',
        primary_address_postcode='SE10 9NN',
        primary_address_country=_construct_mock(
            id='80756b9a-5d95-e211-a939-e4115bead28a',
            name='United Kingdom',
        ),
    )
    with pytest.raises(AttributeError):
        dict_utils.address_dict(obj, prefix='secondary_address')


def test_contact_or_adviser_dict():
    """Tests contact_or_adviser_dict."""
    obj = mock.Mock()
    obj.id = 123
    obj.first_name = 'First'
    obj.last_name = 'Last'
    obj.name = 'First Last'

    res = dict_utils.contact_or_adviser_dict(obj)

    assert res == {
        'id': str(obj.id),
        'first_name': obj.first_name,
        'last_name': obj.last_name,
        'name': obj.name,
    }


def test_contact_or_adviser_dict_include_dit_team():
    """Tests contact_or_adviser_dict including its team."""
    obj = mock.Mock()
    obj.id = 123
    obj.first_name = 'First'
    obj.last_name = 'Last'
    obj.name = 'First Last'
    obj.dit_team.id = 321
    obj.dit_team.name = 'team name'

    res = dict_utils.contact_or_adviser_dict(obj, include_dit_team=True)

    assert res == {
        'id': str(obj.id),
        'first_name': obj.first_name,
        'last_name': obj.last_name,
        'name': obj.name,
        'dit_team': {
            'id': '321',
            'name': 'team name',
        },
    }


def test_contact_or_adviser_dict_none_dit_team():
    """Tests contact_or_adviser_dict including its team when dit_team is None."""
    obj = mock.Mock()
    obj.id = 123
    obj.first_name = 'First'
    obj.last_name = 'Last'
    obj.name = 'First Last'
    obj.dit_team = None

    res = dict_utils.contact_or_adviser_dict(obj, include_dit_team=True)

    assert res == {
        'id': str(obj.id),
        'first_name': obj.first_name,
        'last_name': obj.last_name,
        'name': obj.name,
        'dit_team': {},
    }


def test_contact_or_adviser_list_of_dicts():
    """Test that contact_or_adviser_list_of_dicts returns a list of person dicts."""
    data = [
        {'id': '12', 'first_name': 'first A', 'last_name': 'last A', 'name': 'test A'},
        {'id': '99', 'first_name': 'first B', 'last_name': 'last B', 'name': 'testing B'},
    ]
    objects = [mock.Mock(), mock.Mock()]
    for obj, data_item in zip(objects, data):
        obj.configure_mock(**data_item)

    manager = mock.Mock(
        all=mock.Mock(return_value=objects),
    )

    assert dict_utils.contact_or_adviser_list_of_dicts(manager) == data


def test_ch_company_dict():
    """Tests ch_company_dict."""
    obj = mock.Mock()
    obj.id = 123
    obj.company_number = '01234567'

    res = dict_utils.ch_company_dict(obj)

    assert res == {
        'id': str(obj.id),
        'company_number': obj.company_number,
    }


def test_nested_id_name_dict():
    """Tests nested id name dict."""
    obj = mock.Mock()
    obj.company.sector.id = 123
    obj.company.sector.name = 'Cats'

    res = dict_utils.computed_nested_id_name_dict('company.sector')(obj)

    assert res == {
        'id': str(obj.company.sector.id),
        'name': obj.company.sector.name,
    }


def test_nested_id_name_dict_raises_exception_on_invalid_argument():
    """Tests nested id name dict raises exception on invalid argument."""
    obj = mock.Mock()

    with raises(ValueError):
        dict_utils.computed_nested_id_name_dict('company')(obj)


def test_nested_id_name_dict_returns_none_on_invalid_path():
    """Tests nested id name dict raises exception on invalid path.
    We assume that first part of path exists.
    """
    obj = mock.Mock(company=None)

    res = dict_utils.computed_nested_id_name_dict('company.sector')(obj)
    assert res is None
