from decimal import Decimal
from io import BytesIO

import pytest
from django.core.management import call_command

from datahub.interaction.models import ServiceDeliveryStatus
from datahub.interaction.test.factories import CompanyInteractionFactory, ServiceDeliveryFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def statuses():
    """List of statuses in the database."""
    return list(ServiceDeliveryStatus.objects.order_by('?'))


@pytest.fixture
def interactions(statuses):
    """Set of interactions to use as test data."""
    return [
        ServiceDeliveryFactory(
            service_delivery_status=None, grant_amount_offered=None, net_company_receipt=None,
        ),
        ServiceDeliveryFactory(
            service_delivery_status=None, grant_amount_offered=None, net_company_receipt=None,
        ),
        ServiceDeliveryFactory(
            service_delivery_status=statuses[2],
            grant_amount_offered='100.00',
            net_company_receipt='99.99',
        ),
        ServiceDeliveryFactory(
            service_delivery_status=None,
            grant_amount_offered='99.99',
            net_company_receipt=None,
        ),
        ServiceDeliveryFactory(
            service_delivery_status=None,
            grant_amount_offered=None,
            net_company_receipt='99.99',
        ),
        CompanyInteractionFactory(),
    ]


@pytest.fixture
def s3_csv_object(s3_stubber, statuses, interactions):
    """Uses the botocore S3 stubber to return CSV data for a particular bucket and key."""
    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,status_id,grant_offered,net_company_receipt
00000000-0000-0000-0000-000000000000,45329c18-6095-e211-a939-e4115bead28a,250.00,200.00
{interactions[0].pk},{statuses[0].pk},250.00,null
{interactions[1].pk},null,250.00,200.00
{interactions[2].pk},{statuses[0].pk},250.00,200.00
{interactions[3].pk},{statuses[3].pk},333.00,999.99
{interactions[4].pk},{statuses[4].pk},999.99,null
{interactions[5].pk},{statuses[0].pk},2222.22,1111.11
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
    return bucket, object_key


def test_run(statuses, interactions, s3_csv_object, caplog):
    """Test that the command updates the specified records (ignoring ones with errors)."""
    caplog.set_level('ERROR')

    bucket, object_key = s3_csv_object

    call_command('update_service_delivery_grant_fields', bucket, object_key)

    assert len(caplog.records) == 2
    assert 'Interaction matching query does not exist' in caplog.text
    assert 'Cannot set grant fields on interactions without kind==service_delivery' in caplog.text

    for interaction in interactions:
        interaction.refresh_from_db()

    expected_statues = [statuses[0], None, statuses[2], statuses[3], statuses[4], None]
    actual_statuses = [interaction.service_delivery_status for interaction in interactions]
    assert actual_statuses == expected_statues

    expected_grant_amounts_offered = [
        Decimal('250.00'), Decimal('250.00'), Decimal('100.00'), Decimal('99.99'),
        Decimal('999.99'), None,
    ]
    actual_grant_amounts_offered = [
        interaction.grant_amount_offered for interaction in interactions
    ]
    assert actual_grant_amounts_offered == expected_grant_amounts_offered

    expected_net_company_receipts = [
        None, Decimal('200.00'), Decimal('99.99'), Decimal('999.99'),
        Decimal('99.99'), None,
    ]
    actual_expected_net_company_receipts = [
        interaction.net_company_receipt for interaction in interactions
    ]
    assert actual_expected_net_company_receipts == expected_net_company_receipts


def test_overwrite(statuses, interactions, s3_csv_object, caplog):
    """Test that the command overwrites non-null values when --overwrite is passed."""
    caplog.set_level('ERROR')

    bucket, object_key = s3_csv_object

    call_command('update_service_delivery_grant_fields', bucket, object_key, overwrite=True)

    assert len(caplog.records) == 2
    assert 'Interaction matching query does not exist' in caplog.text
    assert 'Cannot set grant fields on interactions without kind==service_delivery' in caplog.text

    for interaction in interactions:
        interaction.refresh_from_db()

    expected_statues = [statuses[0], None, statuses[0], statuses[3], statuses[4], None]
    actual_statuses = [interaction.service_delivery_status for interaction in interactions]
    assert actual_statuses == expected_statues

    expected_grant_amounts_offered = [
        Decimal('250.00'), Decimal('250.00'), Decimal('250.00'), Decimal('333.00'),
        Decimal('999.99'), None,
    ]
    actual_grant_amounts_offered = [
        interaction.grant_amount_offered for interaction in interactions
    ]
    assert actual_grant_amounts_offered == expected_grant_amounts_offered

    expected_net_company_receipts = [
        None, Decimal('200.00'), Decimal('200.00'), Decimal('999.99'), None, None,
    ]
    actual_expected_net_company_receipts = [
        interaction.net_company_receipt for interaction in interactions
    ]
    assert actual_expected_net_company_receipts == expected_net_company_receipts


def test_simulate(statuses, interactions, s3_csv_object, caplog):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('ERROR')

    bucket, object_key = s3_csv_object

    call_command('update_service_delivery_grant_fields', bucket, object_key, simulate=True)

    assert len(caplog.records) == 2
    assert 'Interaction matching query does not exist' in caplog.text
    assert 'Cannot set grant fields on interactions without kind==service_delivery' in caplog.text

    for interaction in interactions:
        interaction.refresh_from_db()

    expected_statues = [None, None, statuses[2], None, None, None]
    actual_statuses = [interaction.service_delivery_status for interaction in interactions]
    assert actual_statuses == expected_statues

    expected_grant_amounts_offered = [None, None, Decimal('100.00'), Decimal('99.99'), None, None]
    actual_grant_amounts_offered = [
        interaction.grant_amount_offered for interaction in interactions
    ]
    assert actual_grant_amounts_offered == expected_grant_amounts_offered

    expected_net_company_receipts = [None, None, Decimal('99.99'), None, Decimal('99.99'), None]
    actual_expected_net_company_receipts = [
        interaction.net_company_receipt for interaction in interactions
    ]
    assert actual_expected_net_company_receipts == expected_net_company_receipts
