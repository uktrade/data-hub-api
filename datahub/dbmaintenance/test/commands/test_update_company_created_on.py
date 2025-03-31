"""Tests for the update_company_uk_region management command."""

from datetime import datetime, timezone
from io import BytesIO

import pytest
from django.core.management import call_command
from freezegun import freeze_time
from reversion.models import Version

from datahub.company.models import Company
from datahub.company.test.factories import CompanyFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'simulate',
    [
        True,
        False,
    ],
)
def test_run(s3_stubber, caplog, simulate):
    """Test the command.

    It should:
    - update records only if simulate=False is passed
    - not update records if simulate=True is passed
    - not update created_on if it exists already
    - ignore rows with unmatched Company UUIDs
    """
    caplog.set_level('WARNING')

    original_created_on = datetime(2017, 1, 1, tzinfo=timezone.utc)

    with freeze_time(original_created_on):
        companies = CompanyFactory.create_batch(2)

    company_with_created_on = companies[0]
    company_without_created_on = companies[1]
    company_without_created_on.created_on = None
    company_without_created_on.save()

    apr_13_2018_str = '13/04/2018'

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""UUID,Suggested Created Date
00000000-0000-0000-0000-000000000000,17/02/2018
{company_with_created_on.pk},19/02/2018
{company_without_created_on.pk},{apr_13_2018_str}
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

    call_command(
        'update_company_created_on',
        bucket,
        object_key,
        simulate=simulate,
    )

    for company in companies:
        company.refresh_from_db()

    log_records = caplog.get_records(when='call')
    assert log_records[0].exc_info[0] == Company.DoesNotExist
    assert log_records[1].msg == (
        f'Company {company_with_created_on.pk} already has a `created_on`; skipping'
    )

    assert company_with_created_on.created_on == original_created_on

    if simulate:
        assert company_without_created_on.created_on is None
    else:
        new_created_on = company_without_created_on.created_on
        d, m, y = new_created_on.day, new_created_on.month, new_created_on.year
        assert (d, m, y) == tuple([int(s) for s in apr_13_2018_str.split('/')])


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created when created_on is set."""
    companies = CompanyFactory.create_batch(2)

    company_with_created_on = companies[0]
    company_without_created_on = companies[1]
    company_without_created_on.created_on = None
    company_without_created_on.save()

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""UUID,Suggested Created Date
{company_without_created_on.pk},19/02/2018
{company_with_created_on.pk},13/04/2018
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

    call_command(
        'update_company_created_on',
        bucket,
        object_key,
        simulate=False,
    )

    versions = Version.objects.get_for_object(company_with_created_on)
    assert versions.count() == 0

    versions = Version.objects.get_for_object(company_without_created_on)
    assert versions.count() == 1
    assert versions[0].revision.get_comment() == 'Created datetime updated.'
