from unittest import mock

from .. import dict_utils


def test_id_name_dict():
    """Tests _id_name_dict."""
    obj = mock.Mock()
    obj.id = 123
    obj.name = 'test'

    res = dict_utils._id_name_dict(obj)

    assert res == {
        'id': str(obj.id),
        'name': obj.name,
    }


def test_id_type_dict():
    """Tests _id_type_dict."""
    obj = mock.Mock()
    obj.id = 123
    obj.type = 'test'

    res = dict_utils._id_type_dict(obj)

    assert res == {
        'id': str(obj.id),
        'type': obj.type,
    }


def test_id_uri_dict():
    """Tests _id_type_dict."""
    obj = mock.Mock()
    obj.id = 123
    obj.uri = 'test'

    res = dict_utils._id_uri_dict(obj)

    assert res == {
        'id': str(obj.id),
        'uri': obj.uri,
    }


def test_contact_dict():
    """Tests contact_dict."""
    obj = mock.Mock()
    obj.id = 123
    obj.first_name = 'First'
    obj.last_name = 'Last'

    res = dict_utils._contact_dict(obj)

    assert res == {
        'id': str(obj.id),
        'first_name': obj.first_name,
        'last_name': obj.last_name,
    }


def test_company_dict():
    """Tests company_dict."""
    obj = mock.Mock()
    obj.id = 123
    obj.company_number = '01234567'

    res = dict_utils._company_dict(obj)

    assert res == {
        'id': str(obj.id),
        'company_number': obj.company_number,
    }
