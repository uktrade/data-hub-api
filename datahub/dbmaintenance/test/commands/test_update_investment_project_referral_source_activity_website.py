from io import BytesIO

import factory
import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.metadata.test.factories import (
    ReferralSourceActivityFactory,
    ReferralSourceWebsiteFactory,
)

pytestmark = pytest.mark.django_db


def test_run(s3_stubber):
    """Test that the command updates the relevant records ignoring ones with errors."""
    referral_source_activities = ReferralSourceActivityFactory.create_batch(5)
    referral_source_websites = ReferralSourceWebsiteFactory.create_batch(5)

    investment_projects = [
        # investment project in CSV doesn't exist so row should fail

        # referral_source_activity and referral_source_website should get updated
        InvestmentProjectFactory(
            referral_source_activity_id=referral_source_activities[0].id,
            referral_source_activity_website=referral_source_websites[0],
        ),
        # referral_source_activity and referral_source_website should get updated
        InvestmentProjectFactory(
            referral_source_activity_id=referral_source_activities[1].id,
            referral_source_activity_website=referral_source_websites[1],
        ),
        # should be ignored
        InvestmentProjectFactory(
            referral_source_activity_id=referral_source_activities[2].id,
            referral_source_activity_website=referral_source_websites[2],
        ),
        # referral_source_activity is invalid so it should fail
        InvestmentProjectFactory(
            referral_source_activity_id=referral_source_activities[3].id,
            referral_source_activity_website=referral_source_websites[3],
        ),
        # referral_source_website is invalid so it should fail
        InvestmentProjectFactory(
            referral_source_activity_id=referral_source_activities[4].id,
            referral_source_activity_website=referral_source_websites[4],
        ),
    ]

    new_referral_activity = ReferralSourceActivityFactory()
    new_referral_website = ReferralSourceWebsiteFactory()

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,referral_source_activity_id,referral_source_activity_website_id
00000000-0000-0000-0000-000000000000,{new_referral_activity.id},NULL
{investment_projects[0].id},{new_referral_activity.id},{new_referral_website.id}
{investment_projects[1].id},{new_referral_activity.id},NULL
{investment_projects[3].id},00000000-0000-0000-0000-000000000000,NULL
{investment_projects[4].id},NULL,00000000-0000-0000-0000-000000000000
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

    call_command('update_investment_project_referral_source_activity_website', bucket, object_key)

    for investment_project in investment_projects:
        investment_project.refresh_from_db()

    assert investment_projects[0].referral_source_activity == new_referral_activity
    assert investment_projects[0].referral_source_activity_website == new_referral_website
    assert investment_projects[1].referral_source_activity == new_referral_activity
    assert investment_projects[1].referral_source_activity_website is None
    assert investment_projects[2].referral_source_activity == referral_source_activities[2]
    assert investment_projects[2].referral_source_activity_website == referral_source_websites[2]
    assert investment_projects[3].referral_source_activity == referral_source_activities[3]
    assert investment_projects[3].referral_source_activity_website == referral_source_websites[3]
    assert investment_projects[4].referral_source_activity == referral_source_activities[4]
    assert investment_projects[4].referral_source_activity_website == referral_source_websites[4]


def test_simulate(s3_stubber):
    """Test that the command only simulates the actions if --simulate is passed in."""
    referral_source_activities = ReferralSourceActivityFactory.create_batch(2)
    referral_source_websites = ReferralSourceWebsiteFactory.create_batch(2)

    investment_projects = InvestmentProjectFactory.create_batch(
        2,
        referral_source_activity_id=factory.Iterator(
            referral_source_activity.id for referral_source_activity in referral_source_activities
        ),
        referral_source_activity_website=factory.Iterator(referral_source_websites),
    )
    new_referral_activity = ReferralSourceActivityFactory()
    new_referral_website = ReferralSourceWebsiteFactory()

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,referral_source_activity_id,referral_source_activity_website_id
{investment_projects[0].id},{new_referral_activity.id},{new_referral_website.id}
{investment_projects[1].id},{new_referral_activity.id},NULL
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

    call_command(
        'update_investment_project_referral_source_activity_website',
        bucket,
        object_key,
        simulate=True,
    )

    for investment_project in investment_projects:
        investment_project.refresh_from_db()

    for i in range(2):
        assert (
            investment_projects[i].referral_source_activity == referral_source_activities[i]
        )
        assert (
            investment_projects[i].referral_source_activity_website == referral_source_websites[i]
        )


def test_audit_log(s3_stubber):
    """Test that audit log is being created."""
    investment_project = InvestmentProjectFactory()
    new_referral_activity = ReferralSourceActivityFactory()
    new_referral_website = ReferralSourceWebsiteFactory()

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,referral_source_activity_id,referral_source_activity_website_id
{investment_project.id},{new_referral_activity.id},{new_referral_website.id}
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

    call_command(
        'update_investment_project_referral_source_activity_website',
        bucket,
        object_key,
    )

    investment_project.refresh_from_db()

    assert investment_project.referral_source_activity == new_referral_activity
    assert investment_project.referral_source_activity_website == new_referral_website

    versions = Version.objects.get_for_object(investment_project)
    assert len(versions) == 1
    assert versions[0].revision.get_comment() == 'ReferralSourceActivityWebsite migration.'
