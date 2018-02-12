from io import BytesIO

import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.company.test.factories import AdviserFactory

pytestmark = pytest.mark.django_db


def test_run(s3_stubber, caplog):
    """Test that the command updates the specified records (ignoring ones with errors)."""
    caplog.set_level('ERROR')

    advisers = [
        AdviserFactory(contact_email='adviser0@test.com'),
        AdviserFactory(contact_email='adviser1@test.com'),
        AdviserFactory(contact_email='adviser2@test.com'),
        AdviserFactory(contact_email=''),
        AdviserFactory(contact_email='adviser4@test.com'),
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,contact_email
00000000-0000-0000-0000-000000000000,adviser9@test.com
{advisers[0].id},invalid_email
{advisers[1].id},adviser1changed@test.com
{advisers[2].id},adviser2@test.com
{advisers[3].id},adviser3changed@test.com
{advisers[4].id},
"""

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(bytes(csv_content, encoding='utf-8'))
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key
        }
    )

    call_command('update_adviser_contact_email', bucket, object_key)

    assert len(caplog.records) == 2
    assert 'Advisor matching query does not exist' in caplog.text
    assert 'Enter a valid email address' in caplog.text

    for adviser in advisers:
        adviser.refresh_from_db()

    expected_emails = [
        'adviser0@test.com', 'adviser1changed@test.com', 'adviser2@test.com',
        'adviser3changed@test.com', '',
    ]
    assert [adviser.contact_email for adviser in advisers] == expected_emails


def test_simulate(s3_stubber, caplog):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('ERROR')

    advisers = [
        AdviserFactory(contact_email='adviser0@test.com'),
        AdviserFactory(contact_email='adviser1@test.com'),
        AdviserFactory(contact_email='adviser2@test.com'),
        AdviserFactory(contact_email=''),
        AdviserFactory(contact_email='adviser4@test.com'),
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,contact_email
00000000-0000-0000-0000-000000000000,adviser9@test.com
{advisers[0].id},invalid_email
{advisers[1].id},adviser1changed@test.com
{advisers[2].id},adviser2@test.com
{advisers[3].id},adviser3changed@test.com
{advisers[4].id},
"""

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(bytes(csv_content, encoding='utf-8'))
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key
        }
    )

    call_command('update_adviser_contact_email', bucket, object_key, simulate=True)

    assert len(caplog.records) == 2
    assert 'Advisor matching query does not exist' in caplog.text
    assert 'Enter a valid email address' in caplog.text

    for adviser in advisers:
        adviser.refresh_from_db()

    expected_emails = [
        'adviser0@test.com', 'adviser1@test.com', 'adviser2@test.com', '', 'adviser4@test.com',

    ]
    assert [adviser.contact_email for adviser in advisers] == expected_emails


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    advisers = [
        AdviserFactory(contact_email='adviser0@test.com'),
        AdviserFactory(contact_email='adviser1@test.com'),
        AdviserFactory(contact_email='adviser2@test.com'),
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,contact_email
{advisers[0].id},invalid_email
{advisers[1].id},adviser1changed@test.com
{advisers[2].id},adviser2@test.com
"""

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(bytes(csv_content, encoding='utf-8'))
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key
        }
    )

    call_command('update_adviser_contact_email', bucket, object_key)

    for adviser in advisers:
        adviser.refresh_from_db()

    versions = Version.objects.get_for_object(advisers[0])
    assert versions.count() == 0

    versions = Version.objects.get_for_object(advisers[1])
    assert versions.count() == 1
    assert versions[0].revision.comment == 'Loaded contact email from spreadsheet.'

    versions = Version.objects.get_for_object(advisers[2])
    assert versions.count() == 0
