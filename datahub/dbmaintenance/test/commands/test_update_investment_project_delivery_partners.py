from io import BytesIO

import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.investment.models import InvestmentDeliveryPartner
from datahub.investment.test.factories import InvestmentProjectFactory

pytestmark = pytest.mark.django_db


def test_run(s3_stubber, caplog):
    """Test that the command updates the specified records (ignoring ones with errors)."""
    caplog.set_level('ERROR')

    delivery_partners = list(InvestmentDeliveryPartner.objects.all()[:10])

    investment_projects = [
        InvestmentProjectFactory(delivery_partners=[]),
        InvestmentProjectFactory(delivery_partners=[]),
        InvestmentProjectFactory(delivery_partners=delivery_partners[0:1]),
        InvestmentProjectFactory(delivery_partners=delivery_partners[1:2]),
        InvestmentProjectFactory(delivery_partners=[]),
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,delivery_partners
00000000-0000-0000-0000-000000000000,
{investment_projects[0].pk},
{investment_projects[1].pk},{delivery_partners[2].pk}
{investment_projects[2].pk},"{delivery_partners[3].pk},{delivery_partners[4].pk}"
{investment_projects[3].pk},
{investment_projects[4].pk},"{delivery_partners[3].pk},{delivery_partners[4].pk}"
"""

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(csv_content.encode(encoding='utf-8'))
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key
        }
    )

    call_command('update_investment_project_delivery_partners', bucket, object_key)

    for project in investment_projects:
        project.refresh_from_db()

    assert 'InvestmentProject matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert [list(project.delivery_partners.all()) for project in investment_projects] == [
        [],
        delivery_partners[2:3],
        delivery_partners[0:1],
        delivery_partners[1:2],
        delivery_partners[3:5],
    ]


def test_simulate(s3_stubber, caplog):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('ERROR')

    delivery_partners = list(InvestmentDeliveryPartner.objects.all()[:10])

    investment_projects = [
        InvestmentProjectFactory(delivery_partners=[]),
        InvestmentProjectFactory(delivery_partners=[]),
        InvestmentProjectFactory(delivery_partners=delivery_partners[0:1]),
        InvestmentProjectFactory(delivery_partners=delivery_partners[1:2]),
        InvestmentProjectFactory(delivery_partners=[]),
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,delivery_partners
00000000-0000-0000-0000-000000000000,
{investment_projects[0].pk},invalid-uuid
{investment_projects[1].pk},{delivery_partners[2].pk}
{investment_projects[2].pk},"{delivery_partners[3].pk},{delivery_partners[4].pk}"
{investment_projects[3].pk},
{investment_projects[4].pk},"{delivery_partners[3].pk},{delivery_partners[4].pk}"
"""

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(csv_content.encode(encoding='utf-8'))
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key
        }
    )

    call_command('update_investment_project_delivery_partners', bucket, object_key, simulate=True)

    for project in investment_projects:
        project.refresh_from_db()

    assert 'InvestmentProject matching query does not exist' in caplog.text
    assert '"invalid-uuid" is not a valid UUID.' in caplog.text
    assert len(caplog.records) == 2

    assert [list(project.delivery_partners.all()) for project in investment_projects] == [
        [], [], delivery_partners[0:1], delivery_partners[1:2], []
    ]


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    delivery_partners = list(InvestmentDeliveryPartner.objects.all()[:10])

    project_with_change = InvestmentProjectFactory(delivery_partners=[])
    project_without_change = InvestmentProjectFactory(delivery_partners=delivery_partners[0:1])

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,delivery_partners
{project_with_change.pk},{delivery_partners[2].pk}
{project_without_change.pk},{delivery_partners[2].pk}
"""

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(csv_content.encode(encoding='utf-8'))
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key
        }
    )

    call_command('update_investment_project_delivery_partners', bucket, object_key)

    versions = Version.objects.get_for_object(project_without_change)
    assert versions.count() == 0

    versions = Version.objects.get_for_object(project_with_change)
    assert versions.count() == 1
    assert versions[0].revision.comment == 'Investment delivery partners migration.'
