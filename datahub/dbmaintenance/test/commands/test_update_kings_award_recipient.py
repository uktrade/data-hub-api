from io import BytesIO

import pytest
from django.core.management import call_command
from freezegun import freeze_time
from reversion.models import Version

from datahub.company.models import Company
from datahub.company.test.factories import CompanyFactory
from datahub.company_activity.models import KingsAwardRecipient
from datahub.company_activity.tests.factories import KingsAwardRecipientFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def company_numbers():
    """Fixture for company numbers."""
    return [CompanyFactory(company_number=f'1000000{i}').company_number for i in range(3)]


@pytest.fixture
def csv_content_base(company_numbers):
    """Fixture for base CSV content."""
    return f"""company_number,year_awarded,category_name,citation,year_expired
{company_numbers[0]},2025,International Trade,Citation 1,2030
{company_numbers[1]},2025,Innovation,Citation 2,2030
{company_numbers[2]},2026,Sustainable Development,Citation 3,2031
"""


@pytest.fixture
def s3_setup(s3_stubber):
    """Common S3 setup function."""

    def _setup(csv_content):
        bucket = 'test_bucket'
        object_key = 'test_key'
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
        return bucket, object_key

    return _setup


@freeze_time('2025-04-01')
def test_create_awards(s3_setup, company_numbers, csv_content_base):
    """Test that the command creates new awards correctly."""
    initial_award_count = KingsAwardRecipient.objects.count()
    bucket, object_key = s3_setup(csv_content_base)

    call_command('update_kings_award_recipient', bucket, object_key)

    final_award_count = KingsAwardRecipient.objects.count()
    assert final_award_count - initial_award_count == 3
    assert KingsAwardRecipient.objects.filter(company__company_number=company_numbers[0]).exists()
    assert KingsAwardRecipient.objects.filter(company__company_number=company_numbers[1]).exists()
    assert KingsAwardRecipient.objects.filter(company__company_number=company_numbers[2]).exists()


@freeze_time('2025-04-01')
def test_update_award(s3_setup, company_numbers, csv_content_base):
    """Test that the command updates an existing award."""
    existing_award = KingsAwardRecipientFactory(
        company=Company.objects.get(company_number=company_numbers[0]),
        year_awarded=2025,
        category=KingsAwardRecipient.Category.INTERNATIONAL_TRADE,
        citation='Initial Citation',
        year_expired=2030,
    )
    initial_award_count = KingsAwardRecipient.objects.count()
    update_row = f'{company_numbers[0]},2025,International Trade,UPDATED Citation 1,2030\n'
    csv_content = csv_content_base + update_row
    bucket, object_key = s3_setup(csv_content)

    call_command('update_kings_award_recipient', bucket, object_key)

    final_award_count = KingsAwardRecipient.objects.count()
    assert final_award_count - initial_award_count == 2

    updated_award = KingsAwardRecipient.objects.get(pk=existing_award.pk)
    assert updated_award.citation == 'UPDATED Citation 1'
    assert KingsAwardRecipient.objects.filter(company__company_number=company_numbers[1]).exists()
    assert KingsAwardRecipient.objects.filter(company__company_number=company_numbers[2]).exists()


@freeze_time('2025-04-01')
def test_skip_missing_company(s3_setup, company_numbers, csv_content_base):
    """Test that rows with non-existent company numbers are skipped."""
    initial_award_count = KingsAwardRecipient.objects.count()
    missing_company_row = '9999999,2025,International Trade,Citation 4,2030\n'
    csv_content = csv_content_base + missing_company_row
    bucket, object_key = s3_setup(csv_content)

    call_command('update_kings_award_recipient', bucket, object_key)

    final_award_count = KingsAwardRecipient.objects.count()
    assert final_award_count - initial_award_count == 3
    assert KingsAwardRecipient.objects.filter(company__company_number=company_numbers[0]).exists()
    assert KingsAwardRecipient.objects.filter(company__company_number=company_numbers[1]).exists()
    assert KingsAwardRecipient.objects.filter(company__company_number=company_numbers[2]).exists()


@freeze_time('2025-04-01')
def test_skip_invalid_category(s3_setup, company_numbers, csv_content_base):
    """Test that rows with invalid category names are skipped."""
    initial_award_count = KingsAwardRecipient.objects.count()
    invalid_category_row = f'{company_numbers[0]},2025,Invalid Category,Citation 5,2030\n'
    csv_content = csv_content_base + invalid_category_row
    bucket, object_key = s3_setup(csv_content)

    call_command('update_kings_award_recipient', bucket, object_key)

    final_award_count = KingsAwardRecipient.objects.count()
    assert final_award_count - initial_award_count == 3
    assert not KingsAwardRecipient.objects.filter(
        company__company_number=company_numbers[0],
        citation='Citation 5',
    ).exists()
    assert KingsAwardRecipient.objects.filter(
        company__company_number=company_numbers[0],
        citation='Citation 1',
    ).exists()
    assert KingsAwardRecipient.objects.filter(company__company_number=company_numbers[1]).exists()
    assert KingsAwardRecipient.objects.filter(company__company_number=company_numbers[2]).exists()


@freeze_time('2025-04-01')
def test_skip_invalid_year_low(s3_setup, company_numbers, csv_content_base):
    """Test that rows with year_awarded below the minimum are skipped."""
    initial_award_count = KingsAwardRecipient.objects.count()
    invalid_year_row = f'{company_numbers[0]},1960,International Trade,Citation 6,2030\n'
    csv_content = csv_content_base + invalid_year_row
    bucket, object_key = s3_setup(csv_content)

    call_command('update_kings_award_recipient', bucket, object_key)

    final_award_count = KingsAwardRecipient.objects.count()
    assert final_award_count - initial_award_count == 3
    assert not KingsAwardRecipient.objects.filter(
        company__company_number=company_numbers[0],
        citation='Citation 6',
    ).exists()
    assert KingsAwardRecipient.objects.filter(
        company__company_number=company_numbers[0],
        citation='Citation 1',
    ).exists()
    assert KingsAwardRecipient.objects.filter(company__company_number=company_numbers[1]).exists()
    assert KingsAwardRecipient.objects.filter(company__company_number=company_numbers[2]).exists()


@freeze_time('2025-04-01')
def test_skip_invalid_year_expired(s3_setup, company_numbers, csv_content_base):
    """Test that rows with year_expired before year_awarded are skipped."""
    initial_award_count = KingsAwardRecipient.objects.count()
    invalid_expiry_row = f'{company_numbers[0]},2025,International Trade,Citation 7,2020\n'
    csv_content = csv_content_base + invalid_expiry_row
    bucket, object_key = s3_setup(csv_content)

    call_command('update_kings_award_recipient', bucket, object_key)

    final_award_count = KingsAwardRecipient.objects.count()
    assert final_award_count - initial_award_count == 3
    assert not KingsAwardRecipient.objects.filter(
        company__company_number=company_numbers[0],
        citation='Citation 7',
    ).exists()
    assert KingsAwardRecipient.objects.filter(
        company__company_number=company_numbers[0],
        citation='Citation 1',
    ).exists()
    assert KingsAwardRecipient.objects.filter(company__company_number=company_numbers[1]).exists()
    assert KingsAwardRecipient.objects.filter(company__company_number=company_numbers[2]).exists()


def test_simulate(s3_stubber, caplog, company_numbers, csv_content_base):
    """Test that the command simulates updates/creations if --simulate is passed in."""
    caplog.set_level('INFO')
    initial_award_count = KingsAwardRecipient.objects.count()

    bucket = 'test_bucket'
    object_key = 'test_key'

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(csv_content_base.encode(encoding='utf-8')),
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key,
        },
    )

    call_command('update_kings_award_recipient', bucket, object_key, simulate=True)

    assert initial_award_count == KingsAwardRecipient.objects.count()
    assert 'succeeded: 3' in caplog.text


def test_audit_log(s3_stubber, company_numbers, csv_content_base):
    """Test that reversion revisions are created for creates and updates."""
    bucket = 'test_bucket'
    object_key = 'test_key'

    # add an update row to test both create and update updates
    update_row = f'{company_numbers[0]},2025,International Trade,UPDATED Citation 1,2030\n'
    csv_content = csv_content_base + update_row

    initial_award = KingsAwardRecipientFactory(
        company=Company.objects.get(company_number=company_numbers[0]),
        year_awarded=2025,
        category=KingsAwardRecipient.Category.INTERNATIONAL_TRADE,
        citation='Initial Citation',
        year_expired=2030,
    )

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

    call_command('update_kings_award_recipient', bucket, object_key)

    # assert updated
    updated_award = KingsAwardRecipient.objects.get(pk=initial_award.pk)
    versions = Version.objects.get_for_object(updated_award)
    assert versions.count() == 2

    # assert created
    created_award_1 = KingsAwardRecipient.objects.get(
        company__company_number=company_numbers[1],
        year_awarded=2025,
    )
    versions = Version.objects.get_for_object(created_award_1)
    assert versions.count() == 1

    created_award_2 = KingsAwardRecipient.objects.get(
        company__company_number=company_numbers[2],
        year_awarded=2026,
    )
    versions = Version.objects.get_for_object(created_award_2)
    assert versions.count() == 1
