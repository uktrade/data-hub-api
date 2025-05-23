import boto3
import pytest
from moto import mock_aws

from datahub.core import constants
from datahub.core.test_utils import create_test_user
from datahub.ingest.constants import (
    AWS_REGION,
    S3_BUCKET_NAME,
)
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.test.factories import (
    EYBLeadFactory,
    eyb_lead_marketing_record_faker,
    eyb_lead_triage_record_faker,
    eyb_lead_user_record_faker,
)
from datahub.metadata.models import (
    Country,
    Sector,
    UKRegion,
)


@pytest.fixture
def test_user_with_view_permissions():
    return create_test_user(permission_codenames=['view_eyblead'])


@pytest.fixture
def eyb_lead_triage_data():
    return eyb_lead_triage_record_faker()


@pytest.fixture
def eyb_lead_user_data():
    return eyb_lead_user_record_faker()


@pytest.fixture
def eyb_lead_marketing_data():
    return eyb_lead_marketing_record_faker()


@pytest.fixture
def eyb_lead_factory_overrides():
    mining_sector = Sector.objects.get(
        pk=constants.Sector.mining_mining_vehicles_transport_equipment.value.id,
    )
    wales_region = UKRegion.objects.get(
        pk=constants.UKRegion.wales.value.id,
    )
    canada_country = Country.objects.get(
        pk=constants.Country.canada.value.id,
    )
    investment_project = InvestmentProjectFactory()
    overrides = {
        'sector': mining_sector,
        'proposed_investment_region': wales_region,
        'address_country': canada_country,
        'investment_projects': [investment_project.id],
    }
    return overrides


@pytest.fixture
def eyb_lead_instance_from_db(eyb_lead_factory_overrides):
    eyb_lead_factory = EYBLeadFactory(**eyb_lead_factory_overrides)
    return EYBLead.objects.get(pk=eyb_lead_factory.pk)


@pytest.fixture
def s3_client(aws_credentials):
    """Fixture for a mocked S3 client.

    Also creates a bucket with the same default name and region used in
    the S3ObjectProcessor class definition. This is because the EYB
    ingestion tasks do not override these values. As a result, it is
    easier to test using the a test bucket with the same name and region.
    """
    with mock_aws():
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        s3_client.create_bucket(
            Bucket=S3_BUCKET_NAME,
            CreateBucketConfiguration={'LocationConstraint': AWS_REGION},
        )
        yield s3_client
