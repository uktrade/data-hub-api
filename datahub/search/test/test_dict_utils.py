from unittest import mock

import pytest
from pytest import raises

from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.core.test_utils import construct_mock
from datahub.search import dict_utils


def test_id_name_dict():
    """Tests _id_name_dict."""
    obj = construct_mock(id=123, name='test')

    res = dict_utils.id_name_dict(obj)

    assert res == {
        'id': str(obj.id),
        'name': obj.name,
    }


def test_interaction_dict():
    """Interaction dict should serialize id, date and subject"""
    obj = construct_mock(
        id=1234,
        date='2018-01-01',
        subject='mock interaction',
    )
    res = dict_utils.interaction_dict(obj)
    assert res == {
        'id': str(obj.id),
        'date': obj.date,
        'subject': obj.subject,
    }


def test_interaction_dict_none():
    """Interaction dict should return none for none input"""
    res = dict_utils.interaction_dict(None)
    assert res is None


def test_id_name_list_of_dicts():
    """Test that id_name_list_of_dicts returns a list of dicts with ID and name keys."""
    data = [
        {'id': '12', 'name': 'test A'},
        {'id': '99', 'name': 'testing B'},
    ]
    objects = [construct_mock(**mock_data) for mock_data in data]

    manager = mock.Mock(
        all=mock.Mock(return_value=objects),
    )

    assert dict_utils.id_name_list_of_dicts(manager) == data


def test_id_type_dict():
    """Tests _id_type_dict."""
    obj = construct_mock(id=123, type='test')

    res = dict_utils.id_type_dict(obj)

    assert res == {
        'id': str(obj.id),
        'type': obj.type,
    }


def test_id_uri_dict():
    """Tests id_uri_dict."""
    obj = construct_mock(id=123, uri='test')

    res = dict_utils.id_uri_dict(obj)

    assert res == {
        'id': str(obj.id),
        'uri': obj.uri,
    }


@pytest.mark.parametrize(
    'obj,expected_dict',
    (
        # complete object
        (
            construct_mock(
                id=123,
                name='Name',
                trading_names=['Trading 1', 'Trading 2'],
            ),
            {
                'id': '123',
                'name': 'Name',
                'trading_names': ['Trading 1', 'Trading 2'],
            },
        ),
        # minimal object
        (
            construct_mock(
                id=123,
                name='Name',
                trading_names=[],
            ),
            {
                'id': '123',
                'name': 'Name',
                'trading_names': [],
            },
        ),
        # None
        (
            None,
            None,
        ),
    ),
)
def test_company_dict(obj, expected_dict):
    """Tests for the company_dict function."""
    company = dict_utils.company_dict(obj)

    assert company == expected_dict


@pytest.mark.parametrize(
    'obj,fields_prefix,expected_address_dict',
    (
        # returns None in case of empty address fields values
        (
            construct_mock(
                address_1='',
                address_2='',
                address_town='',
                address_county='',
                address_postcode='',
                address_country=None,
                address_area=None,
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
            construct_mock(
                primary_address_1='1',
                primary_address_2='Main Road',
                primary_address_town='London',
                primary_address_county='Greenwich',
                primary_address_postcode='SE10 9NN',
                primary_address_country=construct_mock(
                    id='80756b9a-5d95-e211-a939-e4115bead28a',
                    name='United Kingdom',
                ),
                primary_address_area=None,
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
                'area': None,
            },
        ),
        # None values converted to ''
        (
            construct_mock(
                primary_address_1=None,
                primary_address_2=None,
                primary_address_town=None,
                primary_address_county=None,
                primary_address_postcode=None,
                primary_address_country=construct_mock(
                    id='80756b9a-5d95-e211-a939-e4115bead28a',
                    name='United Kingdom',
                ),
                primary_address_area=None,
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
                'area': None,
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
    obj = construct_mock(
        primary_address_1='1',
        primary_address_2='Main Road',
        primary_address_town='London',
        primary_address_county='Greenwich',
        primary_address_postcode='SE10 9NN',
        primary_address_country=construct_mock(
            id='80756b9a-5d95-e211-a939-e4115bead28a',
            name='United Kingdom',
        ),
        primary_address_area=None,
    )
    with pytest.raises(AttributeError):
        dict_utils.address_dict(obj, prefix='secondary_address')


def test_contact_or_adviser_dict():
    """Tests contact_or_adviser_dict."""
    obj = construct_mock(
        id=123,
        first_name='First',
        last_name='Last',
        name='First Last',
    )

    res = dict_utils.contact_or_adviser_dict(obj)

    assert res == {
        'id': str(obj.id),
        'first_name': obj.first_name,
        'last_name': obj.last_name,
        'name': obj.name,
    }


@pytest.mark.parametrize(
    'obj,expected_dict',
    (
        # with dit_team != None
        (
            construct_mock(
                id=123,
                first_name='First',
                last_name='Last',
                name='First Last',
                dit_team=construct_mock(
                    id=321,
                    name='team name',
                ),
            ),
            {
                'id': '123',
                'first_name': 'First',
                'last_name': 'Last',
                'name': 'First Last',
                'dit_team': {
                    'id': '321',
                    'name': 'team name',
                },
            },
        ),
        # with dit_team = None
        (
            construct_mock(
                id=123,
                first_name='First',
                last_name='Last',
                name='First Last',
                dit_team=None,
            ),
            {
                'id': '123',
                'first_name': 'First',
                'last_name': 'Last',
                'name': 'First Last',
                'dit_team': {},
            },
        ),
    ),
)
def test_contact_or_adviser_dict_include_dit_team(obj, expected_dict):
    """Tests contact_or_adviser_dict including its team."""
    res = dict_utils.contact_or_adviser_dict(obj, include_dit_team=True)

    assert res == expected_dict


@pytest.mark.django_db
def test_adviser_list_of_dicts():
    """Test that adviser_list_of_dicts returns a list of person dicts."""
    adviser_1 = AdviserFactory()
    adviser_2 = AdviserFactory()
    data = [
        {'adviser': adviser_1},
        {'adviser': adviser_2},
    ]
    expected_response = [
        {'id': str(adviser_1.id), 'first_name': adviser_1.first_name,
            'last_name': adviser_1.last_name, 'name': adviser_1.name},
        {'id': str(adviser_2.id), 'first_name': adviser_2.first_name,
            'last_name': adviser_2.last_name, 'name': adviser_2.name},
    ]

    assert dict_utils.adviser_list_of_dicts(data) == expected_response


def test_contact_or_adviser_list_of_dicts():
    """Test that contact_or_adviser_list_of_dicts returns a list of person dicts."""
    data = [
        {'id': '12', 'first_name': 'first A', 'last_name': 'last A', 'name': 'test A'},
        {'id': '99', 'first_name': 'first B', 'last_name': 'last B', 'name': 'testing B'},
    ]

    objects = [construct_mock(**data_item) for data_item in data]

    manager = mock.Mock(
        all=mock.Mock(return_value=objects),
    )

    assert dict_utils.contact_or_adviser_list_of_dicts(manager) == data


def test_ch_company_dict():
    """Tests ch_company_dict."""
    obj = construct_mock(id=123, company_number='01234567')

    res = dict_utils.ch_company_dict(obj)

    assert res == {
        'id': str(obj.id),
        'company_number': obj.company_number,
    }


@pytest.mark.parametrize(
    'obj,expected_dict',
    (
        # complete object
        (
            construct_mock(
                company=construct_mock(
                    sector=construct_mock(
                        id=123,
                        name='Cats',
                    ),
                ),
            ),
            {
                'id': '123',
                'name': 'Cats',
            },
        ),
        # None first level field
        (
            construct_mock(
                company=None,
            ),
            None,
        ),
        # None second level field
        (
            construct_mock(
                company=construct_mock(
                    sector=None,
                ),
            ),
            None,
        ),
    ),
)
def test_nested_id_name_dict(obj, expected_dict):
    """Tests nested id name dict."""
    res = dict_utils.computed_nested_id_name_dict('company.sector')(obj)

    assert res == expected_dict


def test_nested_id_name_dict_raises_exception_on_invalid_argument():
    """Tests nested id name dict raises exception on invalid argument."""
    obj = mock.Mock()

    with raises(ValueError):
        dict_utils.computed_nested_id_name_dict('company')(obj)


def test_computed_field_function():
    """Tests if provided function is being called and dictionary created."""
    obj = construct_mock(
        get_cats_name=lambda: construct_mock(id='cat-01', name='Mittens'),
    )

    result = dict_utils.computed_field_function('get_cats_name', dict_utils.id_name_dict)(obj)
    assert result == {'id': 'cat-01', 'name': 'Mittens'}


def test_computed_field_function_missing_function():
    """Tests when provided function is missing, ValueError is raised."""
    obj = construct_mock()

    with raises(ValueError):
        dict_utils.computed_field_function('get_cats_name', dict_utils.id_name_dict)(obj)


def test_computed_field_function_not_a_function():
    """Tests when provided function is missing, ValueError is raised."""
    obj = construct_mock(
        get_cats_name='tabby',
    )

    with raises(ValueError):
        dict_utils.computed_field_function('get_cats_name', dict_utils.id_name_dict)(obj)


def test_empty_string_to_null_when_obj_is_falsey():
    """Tests _id_name_dict."""
    res = dict_utils.empty_string_to_null('')

    assert res is None


def test_empty_string_to_null_when_obj_is_truthy():
    """Tests _id_name_dict."""
    res = dict_utils.empty_string_to_null('abc')

    assert res == 'abc'


def test_task_company_returns_none_when_no_company_exists():
    task = mock.MagicMock()
    task.get_company.return_value = None

    assert dict_utils.task_company(task) is None


def test_task_company_returns_company_when_company_exists():
    task = mock.MagicMock()
    company = mock.MagicMock()
    task.get_company.return_value = company

    assert dict_utils.task_company(task) == dict_utils.id_name_dict(company)


def test_task_investment_project_dict_returns_none_when_task_investment_project_prop_missing():
    task = mock.MagicMock()
    del task.investment_project

    assert dict_utils.task_investment_project_dict(task) is None


def test_task_investment_project_dict_returns_none_when_task_investment_project_is_none():
    task = mock.MagicMock()
    task.investment_project = None

    assert dict_utils.task_investment_project_dict(task) is None


def test_task_investment_project_dict_returns_investment_project_task():
    task = mock.MagicMock()
    investment_project = mock.MagicMock()
    task.investment_project = investment_project

    assert dict_utils.task_investment_project_dict(task) == dict_utils.investment_project_dict(
        investment_project,
    )


def test_task_interaction_dict_returns_none_when_task_interaction_prop_missing():
    task = mock.MagicMock()
    del task.interaction

    assert dict_utils.task_interaction_dict(task) is None


def test_task_interaction_dict_returns_none_when_task_interaction_is_none():
    task = mock.MagicMock()
    task.interaction = None

    assert dict_utils.task_interaction_dict(task) is None


def test_task_interaction_dict_returns_interaction_task():
    task = mock.MagicMock()
    interaction = mock.MagicMock()
    task.interaction = interaction

    assert dict_utils.task_interaction_dict(task) == dict_utils.interaction_dict(
        interaction,
    )


@pytest.mark.django_db
def test_nested_company_global_account_manager_returns_expected_value():
    investment_project = mock.MagicMock()
    one_list_account_owner = AdviserFactory()
    investment_project.investor_company = CompanyFactory(
        one_list_account_owner=one_list_account_owner,
    )

    assert dict_utils.nested_company_global_account_manager(
        investment_project,
        'investor_company',
    ) == dict_utils.contact_or_adviser_dict(one_list_account_owner)


def test_nested_company_global_account_manager_returns_none_when_prop_missing():
    investment_project = mock.MagicMock()

    investment_project.investor_company = None

    assert (
        dict_utils.nested_company_global_account_manager(investment_project, 'investor_company')
        is None
    )
