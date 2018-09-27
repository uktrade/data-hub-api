from io import BytesIO

import factory
import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.metadata.models import UKRegion

pytestmark = pytest.mark.django_db


def test_run_with_old_regions(s3_stubber, caplog):
    """
    Test that the command updates the specified records, checking if current regions match
    the old regions column.
    """
    caplog.set_level('ERROR')

    regions = list(UKRegion.objects.all())

    old_allow_blank_possible_uk_regions = [False, True, False, True]
    old_uk_region_locations = [[], [], regions[0:2], regions[2:3]]

    investment_projects = InvestmentProjectFactory.create_batch(
        4,
        allow_blank_possible_uk_regions=factory.Iterator(old_allow_blank_possible_uk_regions),
    )

    for project, project_regions in zip(investment_projects, old_uk_region_locations):
        project.uk_region_locations.set(project_regions)

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,allow_blank_possible_uk_regions,old_uk_region_locations,uk_region_locations
00000000-0000-0000-0000-000000000000,true,null,null
{investment_projects[0].pk},true,null,null
{investment_projects[1].pk},false,null,{regions[2].pk}
{investment_projects[2].pk},false,"{regions[0].pk},{regions[1].pk}","{regions[0].pk},{regions[1].pk}"
{investment_projects[3].pk},true,{regions[5].pk},"{regions[0].pk},{regions[1].pk},{regions[2].pk},{regions[3].pk}"
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
        'update_investment_project_possible_uk_regions',
        bucket,
        object_key,
    )

    for project in investment_projects:
        project.refresh_from_db()

    assert 'InvestmentProject matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert [project.allow_blank_possible_uk_regions for project in investment_projects] == [
        True, False, False, True,
    ]
    assert [list(project.uk_region_locations.all()) for project in investment_projects] == [
        [],
        regions[2:3],
        regions[0:2],
        regions[2:3],  # Old region did not match
    ]


def test_run_ignore_old_regions(s3_stubber, caplog):
    """
    Test that the command updates the specified records (ignoring the old regions column).
    """
    caplog.set_level('ERROR')

    regions = list(UKRegion.objects.all())

    old_allow_blank_possible_uk_regions = [False, True, False, True]
    old_uk_region_locations = [[], [], regions[0:2], regions[2:3]]

    investment_projects = InvestmentProjectFactory.create_batch(
        4,
        allow_blank_possible_uk_regions=factory.Iterator(old_allow_blank_possible_uk_regions),
    )

    for project, project_regions in zip(investment_projects, old_uk_region_locations):
        project.uk_region_locations.set(project_regions)

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,allow_blank_possible_uk_regions,uk_region_locations
00000000-0000-0000-0000-000000000000,true,null
{investment_projects[0].pk},true,null
{investment_projects[1].pk},false,{regions[2].pk}
{investment_projects[2].pk},false,"{regions[0].pk},{regions[1].pk}"
{investment_projects[3].pk},true,"{regions[0].pk},{regions[1].pk},{regions[2].pk},{regions[3].pk}"
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
        'update_investment_project_possible_uk_regions',
        bucket,
        object_key,
        ignore_old_regions=True,
    )

    for project in investment_projects:
        project.refresh_from_db()

    assert 'InvestmentProject matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert [project.allow_blank_possible_uk_regions for project in investment_projects] == [
        True, False, False, True,
    ]
    assert [list(project.uk_region_locations.all()) for project in investment_projects] == [
        [], regions[2:3], regions[0:2], regions[0:4],
    ]


def test_simulate(s3_stubber, caplog):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('ERROR')

    regions = list(UKRegion.objects.all())

    old_allow_blank_possible_uk_regions = [False, True, False, True]
    old_uk_region_locations = [[], [], regions[0:2], regions[2:3]]

    investment_projects = InvestmentProjectFactory.create_batch(
        4,
        allow_blank_possible_uk_regions=factory.Iterator(old_allow_blank_possible_uk_regions),
    )

    for project, project_regions in zip(investment_projects, old_uk_region_locations):
        project.uk_region_locations.set(project_regions)

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,allow_blank_possible_uk_regions,uk_region_locations
00000000-0000-0000-0000-000000000000,true,null
{investment_projects[0].pk},true,null
{investment_projects[1].pk},false,{regions[2].pk}
{investment_projects[2].pk},false,"{regions[0].pk},{regions[1].pk}"
{investment_projects[3].pk},true,"{regions[0].pk},{regions[1].pk},{regions[2].pk},{regions[3].pk}"
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
        'update_investment_project_possible_uk_regions',
        bucket,
        object_key,
        simulate=True,
        ignore_old_regions=True,
    )

    for project in investment_projects:
        project.refresh_from_db()

    assert 'InvestmentProject matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert [project.allow_blank_possible_uk_regions
            for project in investment_projects] == old_allow_blank_possible_uk_regions
    assert [list(project.uk_region_locations.all())
            for project in investment_projects] == old_uk_region_locations


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    regions = list(UKRegion.objects.all())

    project_without_change = InvestmentProjectFactory(
        allow_blank_possible_uk_regions=True,
        uk_region_locations=regions[0:1],
    )
    project_with_change = InvestmentProjectFactory(
        allow_blank_possible_uk_regions=False,
        uk_region_locations=[],
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,allow_blank_possible_uk_regions,uk_region_locations
{project_without_change.pk},true,{regions[0].pk}
{project_with_change.pk},true,{regions[2].pk}
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
        'update_investment_project_possible_uk_regions',
        bucket,
        object_key,
        ignore_old_regions=True,
    )

    versions = Version.objects.get_for_object(project_without_change)
    assert versions.count() == 0

    versions = Version.objects.get_for_object(project_with_change)
    assert versions.count() == 1
    assert versions[0].revision.get_comment() == 'Possible UK regions data migration correction.'
