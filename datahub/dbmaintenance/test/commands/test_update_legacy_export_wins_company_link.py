from io import BytesIO
from uuid import uuid4

import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.company.test.factories import CompanyFactory
from datahub.export_win.models import Win
from datahub.export_win.test.factories import WinFactory

pytestmark = pytest.mark.django_db


def test_run(s3_stubber, caplog):
    """Test that the command updates the specified records (ignoring ones with errors)."""
    caplog.set_level('ERROR')
    companies = CompanyFactory.create_batch(4)
    wins = WinFactory.create_batch(4, company=None)

    uuids = [win.id for win in wins]
    company_uuids = [company.id for company in companies]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_contents = ['export_win_id,data_hub_id']
    for uuid, company_uuid in zip(uuids, company_uuids, strict=False):
        csv_contents.append(f'{uuid},{company_uuid}')

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

    call_command('update_legacy_export_wins_company_link', bucket, object_key)

    for uuid, company in zip(uuids, companies, strict=False):
        win = Win.objects.get(id=uuid)
        assert win.company_id == company.id

        versions = Version.objects.get_for_object(win).order_by('revision__date_created')
        assert versions.count() == 2
        comment = versions[0].revision.get_comment()
        assert comment == 'Legacy export wins company migration - before.'
        comment = versions[1].revision.get_comment()
        assert comment == 'Legacy export wins company migration - after.'

    assert f'Company with ID {bad_company_id} does not exist' in caplog.text


def test_simulate(s3_stubber, caplog):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('ERROR')
    companies = CompanyFactory.create_batch(4)
    wins = WinFactory.create_batch(4, company=None)

    uuids = [win.id for win in wins]
    company_uuids = [company.id for company in companies]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_contents = ['export_win_id,data_hub_id']
    for uuid, company_uuid in zip(uuids, company_uuids, strict=False):
        csv_contents.append(f'{uuid},{company_uuid}')

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

    call_command('update_legacy_export_wins_company_link', bucket, object_key, simulate=True)

    for uuid in uuids:
        win = Win.objects.get(id=uuid)
        assert win.company_id is None

        versions = Version.objects.get_for_object(win)
        assert versions.count() == 0

    assert f'Company with ID {bad_company_id} does not exist' in caplog.text
