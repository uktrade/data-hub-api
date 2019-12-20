"""Tests for the update_company_sector management command."""
from datetime import datetime
from io import BytesIO

import factory
import pytest
from django.core.management import call_command
from django.utils.timezone import utc
from freezegun import freeze_time
from reversion.models import Version

from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import random_obj_for_model
from datahub.metadata.models import Sector

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'simulate,overwrite',
    (
        (True, False),
        (False, False),
        (False, True),
    ),
)
def test_run(s3_stubber, caplog, simulate, overwrite):
    """
    Test that the command:

    - updates records if simulate=False is passed
    - doesn't update records if simulate=True is passed
    - only overwrites non-None values if overwrite=True is passed
    - ignores rows with errors
    """
    caplog.set_level('ERROR')

    original_datetime = datetime(2017, 1, 1, tzinfo=utc)

    sector_a, sector_b = Sector.objects.order_by('?')[:2]

    original_sector_ids = [
        sector_a.pk,
        None,
        sector_a.pk,
        sector_a.pk,
        sector_a.pk,
    ]

    with freeze_time(original_datetime):
        companies = CompanyFactory.create_batch(
            len(original_sector_ids),
            sector_id=factory.Iterator(original_sector_ids),
        )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,sector_id
00000000-0000-0000-0000-000000000000,ongoing
{companies[0].pk},invalid
{companies[1].pk},{sector_a.pk}
{companies[2].pk},{sector_a.pk}
{companies[3].pk},{sector_b.pk}
{companies[4].pk},
"""

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

    with freeze_time('2018-11-11 00:00:00'):
        call_command(
            'update_company_sector',
            bucket,
            object_key,
            simulate=simulate,
            overwrite=overwrite,
        )

    for company in companies:
        company.refresh_from_db()

    assert 'Company matching query does not exist' in caplog.text
    assert 'Must be a valid UUID.' in caplog.text
    assert len(caplog.records) == 2

    if simulate:
        assert [company.sector_id for company in companies] == original_sector_ids
    else:
        expected_sector_ids = [
            sector_a.pk,  # no change as the new value wasn't valid
            sector_a.pk,
            sector_a.pk,  # unchanged
            sector_b.pk if overwrite else sector_a.pk,
            None if overwrite else sector_a.pk,
        ]
        assert [company.sector_id for company in companies] == expected_sector_ids

    assert all(company.modified_on == original_datetime for company in companies)


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created for updated rows."""
    sector = random_obj_for_model(Sector)
    company_without_change = CompanyFactory(sector_id=sector.pk)
    company_with_change = CompanyFactory(sector_id=None)

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,sector_id
{company_without_change.pk},{sector.pk}
{company_with_change.pk},{sector.pk}
"""

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

    call_command('update_company_sector', bucket, object_key)

    versions = Version.objects.get_for_object(company_without_change)
    assert versions.count() == 0

    versions = Version.objects.get_for_object(company_with_change)
    assert versions.count() == 1
    assert versions[0].revision.get_comment() == 'Sector updated.'
