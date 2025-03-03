from io import BytesIO

import pytest
import reversion
from django.core.management import call_command

from datahub.company.test.factories import CompanyFactory
from datahub.company.test.factories import SubsidiaryFactory
pytestmark = pytest.mark.django_db


def test_merge_id_duns_number(s3_stubber):
    """
    Test that the command merge id and duns number
    """
    with reversion.create_revision():
        company_1 = CompanyFactory(duns_number='123456789')
        company_2 = CompanyFactory(duns_number='223456789')
        company_3 = CompanyFactory(transferred_to=None)
        company_4 = CompanyFactory(transferred_to=None)

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = (
        'id,duns\n'
        f'{company_3.id},{company_1.duns_number}\n'
        f'{company_4.id},{company_2.duns_number}\n'
    )

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(bytes(csv_content, encoding='utf-8')),
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key,
        },
    )

    call_command(
        'company_merge_duns_number',
        bucket,
        object_key,
        simulate=False,
    )

    company_3.refresh_from_db()
    company_4.refresh_from_db()
    assert company_3.transferred_to == company_1
    assert company_4.transferred_to == company_2


def test_logs_contain_errors(s3_stubber, caplog):
    """Tests errors are captured in the logs"""
    caplog.set_level('INFO')
    global_company = CompanyFactory()
    company_source = CompanyFactory(
        global_headquarters=global_company,
    )
    company_with_duns = CompanyFactory(duns_number='12345678', archived=True)

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,duns
{company_source.id},{company_with_duns.duns_number}
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

    call_command('company_merge_duns_number', bucket, object_key)

    assert 'List of Target Companies Archived: ' in caplog.text
    assert str(company_with_duns.id) in caplog.text
    assert 'List of Source Compnies with Global Headqaurters: ' in caplog.text
    assert str(company_source.id)


def test_subsidiary_logs(s3_stubber, caplog):
    """Tests subsidiary errors are captured in the logs"""
    caplog.set_level('INFO')
    company = CompanyFactory()
    SubsidiaryFactory(global_headquarters=company)
    company_with_duns = CompanyFactory(duns_number='12345678')
    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,duns
{company.id},{company_with_duns.duns_number}
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

    call_command('company_merge_duns_number', bucket, object_key)

    assert 'List of Source Companies with Subsidiaries: ' in caplog.text
    assert f"{str(company.id)}" in caplog.text


def test_non_subsidiary_logs(s3_stubber, caplog):
    """Tests subsidiary list in log is empty"""
    caplog.set_level('INFO')
    non_subsidiary_company = CompanyFactory()
    company_with_duns = CompanyFactory(duns_number='12345678')

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,duns
{non_subsidiary_company.id},{company_with_duns.duns_number}
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

    call_command('company_merge_duns_number', bucket, object_key)

    assert 'List of Source Companies with Subsidiaries: []' in caplog.text
