from io import BytesIO

import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.company.test.factories import CompanyFactory
from datahub.investment.test.factories import InvestmentProjectFactory

pytestmark = pytest.mark.django_db


def test_run(s3_stubber):
    """Test that the command updates the relevant records ignoring ones with errors."""
    companies = CompanyFactory.create_batch(18)

    investment_projects = [
        # investment project in CSV doesn't exist so row should fail

        # fields should get updated
        InvestmentProjectFactory(
            investor_company=None,
            intermediate_company=None,
            uk_company=None,
            uk_company_decided=False,
        ),
        # should be ignored
        InvestmentProjectFactory(
            investor_company=companies[0],
            intermediate_company=companies[1],
            uk_company=companies[2],
            uk_company_decided=True,
        ),
        # investor_company_id is invalid so it should fail
        InvestmentProjectFactory(
            investor_company=companies[3],
            intermediate_company=companies[4],
            uk_company=companies[5],
            uk_company_decided=True,
        ),
        # intermediate_company_id is invalid so it should fail
        InvestmentProjectFactory(
            investor_company=companies[6],
            intermediate_company=companies[7],
            uk_company=companies[8],
            uk_company_decided=True,
        ),
        # uk_company_id is invalid so it should fail
        InvestmentProjectFactory(
            investor_company=companies[9],
            intermediate_company=companies[10],
            uk_company=companies[11],
            uk_company_decided=True,
        ),
        # uk_company_decided is invalid so it should fail
        InvestmentProjectFactory(
            investor_company=companies[12],
            intermediate_company=companies[13],
            uk_company=companies[14],
            uk_company_decided=True,
        ),
        # company fields NULL and uk_company_decided 0
        InvestmentProjectFactory(
            investor_company=companies[15],
            intermediate_company=companies[16],
            uk_company=companies[17],
            uk_company_decided=True,
        ),

    ]

    file_companies = CompanyFactory.create_batch(3)

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,investor_company_id,intermediate_company_id,uk_company_id,uk_company_decided
00000000-0000-0000-0000-000000000000,NULL,NULL,NULL,NULL
{investment_projects[0].id},{file_companies[0].pk},{file_companies[1].pk},{file_companies[2].pk},1
{investment_projects[2].id},invalid_id,{file_companies[1].pk},{file_companies[2].pk},0
{investment_projects[3].id},{file_companies[0].pk},invalid_id,{file_companies[2].pk},0
{investment_projects[4].id},{file_companies[0].pk},{file_companies[1].pk},invalid_id,0
{investment_projects[5].id},{file_companies[0].pk},{file_companies[1].pk},{file_companies[2].pk},THIS
{investment_projects[6].id},NULL,NULL,NULL,0
"""

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

    call_command('update_investment_project_company', bucket, object_key)

    for investment_project in investment_projects:
        investment_project.refresh_from_db()

    assert investment_projects[0].investor_company == file_companies[0]
    assert investment_projects[0].intermediate_company == file_companies[1]
    assert investment_projects[0].uk_company == file_companies[2]
    assert investment_projects[0].uk_company_decided is True
    assert investment_projects[1].investor_company == companies[0]
    assert investment_projects[1].intermediate_company == companies[1]
    assert investment_projects[1].uk_company == companies[2]
    assert investment_projects[1].uk_company_decided is True
    assert investment_projects[2].investor_company == companies[3]
    assert investment_projects[2].intermediate_company == companies[4]
    assert investment_projects[2].uk_company == companies[5]
    assert investment_projects[2].uk_company_decided is True
    assert investment_projects[3].investor_company == companies[6]
    assert investment_projects[3].intermediate_company == companies[7]
    assert investment_projects[3].uk_company == companies[8]
    assert investment_projects[3].uk_company_decided is True
    assert investment_projects[4].investor_company == companies[9]
    assert investment_projects[4].intermediate_company == companies[10]
    assert investment_projects[4].uk_company == companies[11]
    assert investment_projects[4].uk_company_decided is True
    assert investment_projects[5].investor_company == companies[12]
    assert investment_projects[5].intermediate_company == companies[13]
    assert investment_projects[5].uk_company == companies[14]
    assert investment_projects[5].uk_company_decided is True
    assert investment_projects[6].investor_company is None
    assert investment_projects[6].intermediate_company is None
    assert investment_projects[6].uk_company is None
    assert investment_projects[6].uk_company_decided is False


def test_simulate(s3_stubber):
    """Test that the command only simulates the actions if --simulate is passed in."""
    companies = CompanyFactory.create_batch(3)
    investment_projects = InvestmentProjectFactory.create_batch(
        2,
        investor_company=companies[0],
        intermediate_company=companies[1],
        uk_company=companies[2],
        uk_company_decided=True,
    )
    file_companies = CompanyFactory.create_batch(3)

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,investor_company_id,intermediate_company_id,uk_company_id,uk_company_decided
{investment_projects[0].id},{file_companies[0].pk},{file_companies[1].pk},{file_companies[2].pk},1
{investment_projects[1].id},{file_companies[0].pk},{file_companies[1].pk},{file_companies[2].pk},1
"""
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

    call_command('update_investment_project_company', bucket, object_key, simulate=True)

    for investment_project in investment_projects:
        investment_project.refresh_from_db()

    assert investment_projects[0].investor_company == companies[0]
    assert investment_projects[0].intermediate_company == companies[1]
    assert investment_projects[0].uk_company == companies[2]
    assert investment_projects[0].uk_company_decided is True
    assert investment_projects[1].investor_company == companies[0]
    assert investment_projects[1].intermediate_company == companies[1]
    assert investment_projects[1].uk_company == companies[2]
    assert investment_projects[1].uk_company_decided is True


def test_audit_log(s3_stubber):
    """Test that the audit log is being created."""
    investment_project = InvestmentProjectFactory()
    file_companies = CompanyFactory.create_batch(3)

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,investor_company_id,intermediate_company_id,uk_company_id,uk_company_decided
{investment_project.id},{file_companies[0].pk},{file_companies[1].pk},{file_companies[2].pk},1
"""
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

    call_command('update_investment_project_company', bucket, object_key)

    investment_project.refresh_from_db()

    assert investment_project.investor_company == file_companies[0]
    assert investment_project.intermediate_company == file_companies[1]
    assert investment_project.uk_company == file_companies[2]
    assert investment_project.uk_company_decided is True

    versions = Version.objects.get_for_object(investment_project)
    assert len(versions) == 1
    assert versions[0].revision.get_comment() == 'Companies data migration.'
