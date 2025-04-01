from io import BytesIO
from uuid import uuid4

import pytest
from django.core.management import call_command

from datahub.company.test.factories import CompanyFactory
from datahub.export_win.models import LegacyExportWinsToDataHubCompany

pytestmark = pytest.mark.django_db


def test_run(s3_stubber, caplog):
    """Test that the command updates the specified records (ignoring ones with errors)."""
    caplog.set_level('ERROR')
    companies = CompanyFactory.create_batch(4)
    existing_mapping = LegacyExportWinsToDataHubCompany(id=uuid4())
    existing_mapping.save()
    uuids = [existing_mapping.id, *(uuid4() for _ in range(4))]
    companies.append(None)

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_contents = ['export_win_id,data_hub_id']
    for uuid, company in zip(uuids, companies, strict=False):
        csv_contents.append(f'{uuid},{company.id if company else ""}')

    bad_company_id = uuid4()
    csv_contents.append(f'{uuid4()},{bad_company_id}')

    csv_content = '\n'.join(csv_contents)

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(csv_content.encode(encoding='utf-8')),
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key,
        },
    )

    call_command('update_legacy_export_wins_mapping', bucket, object_key)

    mappings = LegacyExportWinsToDataHubCompany.objects.all()
    assert mappings.count() == 5

    for mapping, uuid, company in zip(mappings, uuids, companies, strict=False):
        assert (company is None and mapping.company_id is None) or (
            mapping.company_id == company.id
        )
        assert mapping.id == uuid

    assert f'Company with ID {bad_company_id} does not exist' in caplog.text


def test_simulate(s3_stubber, caplog):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('ERROR')

    companies = CompanyFactory.create_batch(4)
    uuids = [uuid4() for _ in range(4)]
    companies.append(None)

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_contents = ['export_win_id,data_hub_id']
    csv_contents.append(f'{uuid4()},{uuid4()}')
    for uuid, company in zip(uuids, companies, strict=False):
        csv_contents.append(f'{uuid},{company.id if company else ""}')

    csv_content = '\n'.join(csv_contents)

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(csv_content.encode(encoding='utf-8')),
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key,
        },
    )

    call_command('update_legacy_export_wins_mapping', bucket, object_key, simulate=True)

    mappings = LegacyExportWinsToDataHubCompany.objects.all()

    assert not mappings.exists()

    assert 'Company matching query does not exist' in caplog.text
    assert len(caplog.records) == 1
