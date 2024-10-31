from io import BytesIO
from uuid import uuid4

import pytest
from django.core.management import call_command

from reversion.models import Version

from datahub.company.test.factories import ExportExperienceFactory
from datahub.export_win.models import Win
from datahub.export_win.test.factories import WinFactory


pytestmark = pytest.mark.django_db


def test_run(s3_stubber, caplog):
    """Test that the command updates the specified records (ignoring ones with errors)."""
    caplog.set_level('ERROR')
    wins = WinFactory.create_batch(4, company=None)

    uuids = [win.id for win in wins]
    export_experiences = ExportExperienceFactory.create_batch(4)

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_contents = ['export_win_id,export_experience_id']
    for uuid, export_experience in zip(uuids, export_experiences):
        csv_contents.append(f'{uuid},{export_experience.id}')

    csv_contents.append(f'{uuid4()},{uuid4()}')

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

    call_command('update_legacy_export_wins_export_experience', bucket, object_key)

    for uuid, export_experience in zip(uuids, export_experiences):
        win = Win.objects.get(id=uuid)
        assert win.export_experience_id == export_experience.id

        versions = Version.objects.get_for_object(win).order_by('revision__date_created')
        assert versions.count() == 2
        comment = versions[0].revision.get_comment()
        assert comment == 'Legacy export wins export experience migration - before.'
        comment = versions[1].revision.get_comment()
        assert comment == 'Legacy export wins export experience migration - after.'

    assert 'Win matching query does not exist.' in caplog.text


def test_simulate(s3_stubber, caplog):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('ERROR')
    wins = WinFactory.create_batch(4, company=None)

    uuids = [win.id for win in wins]
    export_experiences = ExportExperienceFactory.create_batch(4)

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_contents = ['export_win_id,export_experience_id']
    for uuid, export_experience in zip(uuids, export_experiences):
        csv_contents.append(f'{uuid},{export_experience.id}')

    csv_contents.append(f'{uuid4()},{uuid4()}')

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

    call_command('update_legacy_export_wins_export_experience', bucket, object_key, simulate=True)

    for uuid, export_experience in zip(uuids, export_experiences):
        win = Win.objects.get(id=uuid)
        assert win.export_experience_id != export_experience.id

        versions = Version.objects.get_for_object(win).order_by('revision__date_created')
        assert versions.count() == 0

    assert 'Win matching query does not exist.' in caplog.text
