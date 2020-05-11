from unittest import mock

import pytest
from django.core.management import call_command

from datahub.company.test.factories import CompanyFactory


pytestmark = pytest.mark.django_db


@pytest.fixture
def mock_create_investigation(monkeypatch):
    """
    Test fixture to mock create_investigation utility.
    """
    mocked_create_investigation = mock.Mock()
    monkeypatch.setattr(
        'datahub.dnb_api.management.commands.submit_legacy_dnb_investigations.'
        'create_investigation',
        mocked_create_investigation,
    )
    return mocked_create_investigation


def test_no_companies_no_investigations_created(mock_create_investigation):
    """
    Test that calling the management command when there are no companies results
    in no `create_investigation` calls.
    """
    call_command('submit_legacy_dnb_investigations')
    assert mock_create_investigation.call_count == 0


def test_legacy_investigations_submitted(mock_create_investigation):
    """
    Test that investigations are submitted as expected when we have a variety
    of company data in the database.
    """
    mocked_investigation_ids = [
        '22222222-2222-3333-4444-555555555555', '33333333-2222-3333-4444-555555555555',
    ]
    mock_create_investigation.side_effect = [
        {'id': mocked_id}
        for mocked_id in mocked_investigation_ids
    ]
    legacy_investigation_companies = [
        CompanyFactory(
            pending_dnb_investigation=True,
            website='',
            dnb_investigation_data={'telephone_number': '1234'},
        ),
        CompanyFactory(
            pending_dnb_investigation=True,
            website=None,
            dnb_investigation_data={'telephone_number': '5678'},
        ),
    ]
    # Companies that should be ignored by the management command
    CompanyFactory(
        pending_dnb_investigation=False,
    )
    CompanyFactory(
        pending_dnb_investigation=True,
        website='http://www.example.com/',
    )
    CompanyFactory(
        pending_dnb_investigation=True,
        website='',
        dnb_investigation_id='11111111-2222-3333-4444-555555555555',
    )
    call_command('submit_legacy_dnb_investigations')
    assert mock_create_investigation.call_count == len(legacy_investigation_companies)

    for company in legacy_investigation_companies:
        mock_create_investigation.assert_any_call(
            {
                'company_details': {
                    'primary_name': company.name,
                    'website': '',
                    'telephone_number': company.dnb_investigation_data['telephone_number'],
                    'address_line_1': company.address_1,
                    'address_line_2': company.address_2,
                    'address_town': company.address_town,
                    'address_county': company.address_county,
                    'address_postcode': company.address_postcode,
                    'address_country': company.address_country.iso_alpha2_code,
                },
            },
        )
        company.refresh_from_db()
        assert str(company.dnb_investigation_id) in mocked_investigation_ids


def test_simulate(caplog, mock_create_investigation):
    """
    Test that the simulate flag logs messages as expected.
    """
    caplog.set_level('INFO')
    company = CompanyFactory(
        pending_dnb_investigation=True,
        website='',
        dnb_investigation_data={'telephone_number': '1234'},
    )
    call_command('submit_legacy_dnb_investigations', simulate=True)
    assert mock_create_investigation.call_count == 0
    expected_message = (
        f'[SIMULATE] Submitting investigation for company ID "{company.id}" to dnb-service.'
    )
    assert expected_message in caplog.text
