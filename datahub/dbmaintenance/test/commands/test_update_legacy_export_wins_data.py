from io import BytesIO

import pytest
from django.core.management import call_command
from faker import Faker
from reversion.models import Version

from datahub.export_win.models import Win
from datahub.export_win.test.factories import WinFactory

pytestmark = pytest.mark.django_db


def test_run(s3_stubber, caplog):
    """Test that the command updates the specified records (ignoring ones with errors)."""
    caplog.set_level('ERROR')

    fake = Faker()
    wins = WinFactory.create_batch(4, company=None)

    uuids = [win.id for win in wins]
    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_contents = [
        'id,company_name,lead_officer_name,lead_officer_email_address,user_name,'
        'user_email,line_manager_name,customer_name,customer_job_title,'
        'customer_email_address',
    ]
    company_names = [fake.company() for _ in range(4)]
    lead_officer_names = [fake.name() for _ in range(4)]
    lead_officer_email_addresses = [fake.email() for _ in range(4)]
    user_names = [fake.name() for _ in range(4)]
    user_emails = [fake.email() for _ in range(4)]
    line_manager_names = [fake.name() for _ in range(4)]
    customer_names = [fake.name() for _ in range(4)]
    customer_job_titles = [fake.job() for _ in range(4)]
    customer_email_addresses = [fake.email() for _ in range(4)]

    for (
        uuid,
        company_name,
        lead_officer_name,
        lead_officer_email_address,
        user_name, user_email,
        line_manager_name,
        customer_name,
        customer_job_title,
        customer_email_address,
    ) in zip(
        uuids,
        company_names,
        lead_officer_names,
        lead_officer_email_addresses,
        user_names,
        user_emails,
        line_manager_names,
        customer_names,
        customer_job_titles,
        customer_email_addresses, strict=False,
    ):
        csv_contents.append(f'{uuid},"{company_name}",{lead_officer_name},'
                            f'{lead_officer_email_address},{user_name},'
                            f'{user_email},{line_manager_name},{customer_name},'
                            f'"{customer_job_title}",{customer_email_address}')

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

    call_command('update_legacy_export_wins_data', bucket, object_key)

    for (
        uuid,
        company_name,
        lead_officer_name,
        lead_officer_email_address,
        user_name, user_email,
        line_manager_name,
        customer_name,
        customer_job_title,
        customer_email_address,
    ) in zip(
        uuids,
        company_names,
        lead_officer_names,
        lead_officer_email_addresses,
        user_names,
        user_emails,
        line_manager_names,
        customer_names,
        customer_job_titles,
        customer_email_addresses, strict=False,
    ):
        win = Win.objects.get(id=uuid)
        assert win.company_name == company_name
        assert win.lead_officer_name == lead_officer_name
        assert win.lead_officer_email_address == lead_officer_email_address
        assert win.adviser_name == user_name
        assert win.adviser_email_address == user_email
        assert win.line_manager_name == line_manager_name
        assert win.customer_name == customer_name
        assert win.customer_job_title == customer_job_title
        assert win.customer_email_address == customer_email_address

        versions = Version.objects.get_for_object(win).order_by('revision__date_created')
        assert versions.count() == 2
        comment = versions[0].revision.get_comment()
        assert comment == 'Legacy export wins data migration - before.'
        comment = versions[1].revision.get_comment()
        assert comment == 'Legacy export wins data migration - after.'


def test_simulate(s3_stubber, caplog):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('ERROR')

    fake = Faker()
    wins = WinFactory.create_batch(4, company=None)

    uuids = [win.id for win in wins]
    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_contents = [
        'id,company_name,lead_officer_name,lead_officer_email_address,user_name,'
        'user_email,line_manager_name,customer_name,customer_job_title, '
        'customer_email_address',
    ]
    company_names = [f'"{fake.company()}"' for _ in range(4)]
    lead_officer_names = [fake.name() for _ in range(4)]
    lead_officer_email_addresses = [fake.email() for _ in range(4)]
    user_names = [fake.name() for _ in range(4)]
    user_emails = [fake.email() for _ in range(4)]
    line_manager_names = [fake.name() for _ in range(4)]
    customer_names = [fake.name() for _ in range(4)]
    customer_job_titles = [fake.job() for _ in range(4)]
    customer_email_addresses = [fake.email() for _ in range(4)]

    for (
        uuid,
        company_name,
        lead_officer_name,
        lead_officer_email_address,
        user_name, user_email,
        line_manager_name,
        customer_name,
        customer_job_title,
        customer_email_address,
    ) in zip(
        uuids,
        company_names,
        lead_officer_names,
        lead_officer_email_addresses,
        user_names,
        user_emails,
        line_manager_names,
        customer_names,
        customer_job_titles,
        customer_email_addresses, strict=False,
    ):
        csv_contents.append(f'{uuid},"{company_name}",{lead_officer_name},'
                            f'{lead_officer_email_address},{user_name},'
                            f'{user_email},{line_manager_name},{customer_name},'
                            f'"{customer_job_title}",{customer_email_address}')

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

    call_command('update_legacy_export_wins_data', bucket, object_key, simulate=True)

    for (
        uuid,
        company_name,
        lead_officer_name,
        lead_officer_email_address,
        user_name, user_email,
        line_manager_name,
        customer_name,
        customer_job_title,
        customer_email_address,
    ) in zip(
        uuids,
        company_names,
        lead_officer_names,
        lead_officer_email_addresses,
        user_names,
        user_emails,
        line_manager_names,
        customer_names,
        customer_job_titles,
        customer_email_addresses, strict=False,
    ):
        win = Win.objects.get(id=uuid)
        assert win.company_name != company_name
        assert win.lead_officer_name != lead_officer_name
        assert win.lead_officer_email_address != lead_officer_email_address
        assert win.adviser_name != user_name
        assert win.adviser_email_address != user_email
        assert win.line_manager_name != line_manager_name
        assert win.customer_name != customer_name
        assert win.customer_job_title != customer_job_title
        assert win.customer_email_address != customer_email_address

        versions = Version.objects.get_for_object(win)
        assert versions.count() == 0
