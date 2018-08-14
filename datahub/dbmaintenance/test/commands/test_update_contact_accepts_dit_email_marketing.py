from datetime import datetime, timezone
from io import BytesIO

import factory
import pytest
from django.core.management import call_command
from freezegun import freeze_time
from reversion.models import Version

from datahub.company.test.factories import ContactFactory

pytestmark = pytest.mark.django_db


def test_run(s3_stubber, caplog):
    """Test that the command updates the specified records (ignoring ones with errors)."""
    caplog.set_level('ERROR')

    original_datetime = datetime(2017, 1, 1, tzinfo=timezone.utc)

    with freeze_time(original_datetime):
        accepts_dit_email_marketing_values = [True, False, True]
        contacts = ContactFactory.create_batch(
            3,
            accepts_dit_email_marketing=factory.Iterator(accepts_dit_email_marketing_values),
        )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,accepts_dit_email_marketing
00000000-0000-0000-0000-000000000000,true
{contacts[0].pk},false
{contacts[1].pk},false
{contacts[2].pk},blah
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

    with freeze_time('2018-11-11 00:00:00'):
        call_command('update_contact_accepts_dit_email_marketing', bucket, object_key)

    for contact in contacts:
        contact.refresh_from_db()

    assert 'Contact matching query does not exist' in caplog.text
    assert '"blah" is not a valid boolean' in caplog.text
    assert len(caplog.records) == 2

    assert [contact.accepts_dit_email_marketing for contact in contacts] == [
        False,
        False,
        True,
    ]
    assert all(contact.modified_on == original_datetime for contact in contacts)


def test_simulate(s3_stubber, caplog):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('ERROR')

    original_datetime = datetime(2017, 1, 1, tzinfo=timezone.utc)

    with freeze_time(original_datetime):
        before_accepts_dit_email_marketing_values = [True, False]
        contacts = ContactFactory.create_batch(
            2,
            accepts_dit_email_marketing=factory.Iterator(
                before_accepts_dit_email_marketing_values,
            ),
        )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,accepts_dit_email_marketing
00000000-0000-0000-0000-000000000000,true
{contacts[0].pk},false
{contacts[1].pk},false
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

    with freeze_time('2018-11-11 00:00:00'):
        call_command(
            'update_contact_accepts_dit_email_marketing', bucket, object_key, simulate=True
        )

    for contact in contacts:
        contact.refresh_from_db()

    assert 'Contact matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    after_accepts_dit_email_marketing_values = [
        contact.accepts_dit_email_marketing for contact in contacts
    ]
    assert after_accepts_dit_email_marketing_values == before_accepts_dit_email_marketing_values


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    contact_without_change = ContactFactory(
        accepts_dit_email_marketing=True,
    )
    contact_with_change = ContactFactory(
        accepts_dit_email_marketing=False,
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,accepts_dit_email_marketing
{contact_without_change.pk},True
{contact_with_change.pk},True
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

    call_command('update_contact_accepts_dit_email_marketing', bucket, object_key)

    versions = Version.objects.get_for_object(contact_without_change)
    assert versions.count() == 0

    versions = Version.objects.get_for_object(contact_with_change)
    assert versions.count() == 1
    assert versions[0].revision.get_comment() == 'Accepts DIT email marketing correction.'
