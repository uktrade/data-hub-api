import pytest
from django.core.cache import cache
from django.test import Client
from django.urls import reverse
from rest_framework import status

from datahub.company.models import Advisor
from datahub.company.test.factories import AdviserFactory
from datahub.core.constants import Team

pytestmark = pytest.mark.django_db


RESET_FIXTURES_URL = reverse('testfixtureapi:reset-fixtures')
CREATE_USER_URL = reverse('testfixtureapi:create-user')
LOAD_FIXTURE_URL = reverse('testfixtureapi:load-fixture')

SEED_USER_DATA = {
    'first_name': 'Seed',
    'last_name': 'User',
    'email': 'seed.user@example.com',
    'token': 'ditStaffToken',
    'dit_team_id': Team.crm.value.id,
    'sso_email_user_id': 'test@user.id',
}

ADVISER_FIXTURE = {
    'model': 'company.advisor',
    'pk': '413a608e-84a4-11e6-ea22-56b6b6499622',
    'fields': {
        'email': 'abc@def',
        'first_name': 'First name',
        'last_name': 'Last name',
        'dit_team': '162a3959-9798-e211-a939-e4115bead28a',
    },
}


def _request_reset_fixtures():
    """Request reset fixtures."""
    return Client().post(RESET_FIXTURES_URL)


def _request_create_user(seed_user_data):
    """Request create user."""
    return Client().post(CREATE_USER_URL, seed_user_data, content_type='application/json')


def _request_load_fixture(fixture):
    """Request load fixture."""
    return Client().post(LOAD_FIXTURE_URL, fixture, content_type='application/json')


def test_reset_fixtures_url_not_found_if_not_setup(settings, caplog):
    """Test that reset fixtures endpoint is not available when it is not set up."""
    caplog.set_level('WARNING')

    settings.ALLOW_TEST_FIXTURE_SETUP = None
    response = _request_reset_fixtures()
    assert response.status_code == status.HTTP_404_NOT_FOUND

    assert caplog.messages == [
        'The `reset_fixture` endpoint is not enabled. The ALLOW_TEST_FIXTURE_SETUP environment'
        ' variable is not set.',
        'Not Found: /testfixtureapi/reset-fixtures/',
    ]


def test_url_found_if_env_setup():
    """Test that reset fixtures endpoint is available when set up."""
    response = _request_reset_fixtures()
    assert response.status_code == status.HTTP_201_CREATED


def test_new_adviser_removed_by_reset_fixtures():
    """Test new adviser is removed by reset fixtures."""
    new_adviser_pk = AdviserFactory().pk
    _request_reset_fixtures()
    with pytest.raises(Advisor.DoesNotExist):
        Advisor.objects.get(pk=new_adviser_pk)


def test_create_user_url_not_found_if_not_setup(settings, caplog):
    """Test that create user endpoint is not available when it is not set up."""
    caplog.set_level('WARNING')

    settings.ALLOW_TEST_FIXTURE_SETUP = None
    response = _request_create_user(SEED_USER_DATA)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    with pytest.raises(Advisor.DoesNotExist):
        Advisor.objects.get(email=SEED_USER_DATA['email'])

    assert caplog.messages == [
        'The `create_user` endpoint is not enabled. The ALLOW_TEST_FIXTURE_SETUP environment'
        ' variable is not set.',
        'Not Found: /testfixtureapi/create-user/',
    ]


def test_create_user_endpoint_creates_user(caplog):
    """Test a user is created by create user."""
    caplog.set_level('INFO')

    _request_create_user(SEED_USER_DATA)
    created_user = Advisor.objects.get(email=SEED_USER_DATA['email'])

    user_data_keys = SEED_USER_DATA.keys() - set(['token'])
    for key in user_data_keys:
        assert str(getattr(created_user, key)) == SEED_USER_DATA[key]

    user_info = [
        'Creating a user: {',
        f'    "dit_team_id": "{SEED_USER_DATA["dit_team_id"]}",',
        f'    "email": "{SEED_USER_DATA["email"]}",',
        f'    "first_name": "{SEED_USER_DATA["first_name"]}",',
        f'    "last_name": "{SEED_USER_DATA["last_name"]}",',
        f'    "sso_email_user_id": "{SEED_USER_DATA["sso_email_user_id"]}"',
        '}',
    ]
    user_token = f'Created a token `{SEED_USER_DATA["token"]}` for user {created_user.id}.'
    assert caplog.messages == [
        '\n'.join(user_info),
        user_token,
    ]


@pytest.mark.usefixtures('local_memory_cache')
def test_created_user_has_token_in_cache():
    """Test that created user has token in the cache."""
    _request_create_user(SEED_USER_DATA)
    token = SEED_USER_DATA['token']
    cache_key = f'access_token:{token}'

    expected_data = {
        'email': SEED_USER_DATA['email'],
        'sso_email_user_id': SEED_USER_DATA['sso_email_user_id'],
    }
    assert cache.get(cache_key) == expected_data


def test_load_fixture_url_not_found_if_not_setup(settings, caplog):
    """Test that load fixture endpoint is not available when it is not set up."""
    caplog.set_level('WARNING')

    settings.ALLOW_TEST_FIXTURE_SETUP = None
    response = _request_load_fixture({'fixture': [ADVISER_FIXTURE]})
    assert response.status_code == status.HTTP_404_NOT_FOUND

    with pytest.raises(Advisor.DoesNotExist):
        Advisor.objects.get(pk=ADVISER_FIXTURE['pk'])

    assert caplog.messages == [
        'The `load_fixture` endpoint is not enabled. The ALLOW_TEST_FIXTURE_SETUP environment'
        ' variable is not set.',
        'Not Found: /testfixtureapi/load-fixture/',
    ]


def test_load_fixture(caplog):
    """Test load fixture endpoint."""
    caplog.set_level('INFO')

    with pytest.raises(Advisor.DoesNotExist):
        Advisor.objects.get(pk=ADVISER_FIXTURE['pk'])

    response = _request_load_fixture({'fixture': [ADVISER_FIXTURE]})

    assert response.status_code == status.HTTP_201_CREATED

    adviser = Advisor.objects.get(pk=ADVISER_FIXTURE['pk'])
    assert adviser.email == ADVISER_FIXTURE['fields']['email']
    assert adviser.first_name == ADVISER_FIXTURE['fields']['first_name']
    assert adviser.last_name == ADVISER_FIXTURE['fields']['last_name']
    assert str(adviser.dit_team_id) == ADVISER_FIXTURE['fields']['dit_team']

    fixture_info = [
        'Loading fixture: [',
        '    {',
        '        "fields": {',
        f'            "dit_team": "{ADVISER_FIXTURE["fields"]["dit_team"]}",',
        f'            "email": "{ADVISER_FIXTURE["fields"]["email"]}",',
        f'            "first_name": "{ADVISER_FIXTURE["fields"]["first_name"]}",',
        f'            "last_name": "{ADVISER_FIXTURE["fields"]["last_name"]}"',
        '        },',
        '        "model": "company.advisor",',
        f'        "pk": "{ADVISER_FIXTURE["pk"]}"',
        '    }',
        ']',
    ]
    assert caplog.messages == ['\n'.join(fixture_info)]
