from io import BytesIO
from uuid import uuid4

import pytest
from django.core.management import call_command
from django.utils import timezone

from reversion.models import Version

from datahub.export_win.models import Win
from datahub.export_win.test.factories import WinFactory


pytestmark = pytest.mark.django_db


def test_run(s3_stubber, caplog):
    """Test that the command updates the specified records (ignoring ones with errors)."""
    caplog.set_level('ERROR')
    wins = WinFactory.create_batch(
        4,
        total_expected_export_value=0,
        total_expected_non_export_value=0,
        total_expected_odi_value=0,
        migrated_on=timezone.now(),
    )
    dh_win = WinFactory(
        total_expected_export_value=0,
        total_expected_non_export_value=0,
        total_expected_odi_value=0,
    )
    uuids = [win.id for win in [*wins, dh_win]]
    total_expected_export_values = [100, 200, 300, 400, 500]
    total_expected_non_export_values = [200, 300, 400, 500, 600]
    total_expected_odi_values = [10, 20, 30, 40, 50]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_contents = ['id,total_expected_export_value,total_expected_non_export_value,'
                    'total_expected_odi_value']
    for uuid, export_value, non_export_value, odi_value in zip(
        uuids,
        total_expected_export_values,
        total_expected_non_export_values,
        total_expected_odi_values,
    ):
        csv_contents.append(f'{uuid},{export_value},{non_export_value},{odi_value}')

    csv_contents.append(f'{uuid4()},0,0,0,0')

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

    call_command('update_legacy_export_wins_totals', bucket, object_key)

    for uuid, export_value, non_export_value, odi_value in zip(
        uuids,
        total_expected_export_values,
        total_expected_non_export_values,
        total_expected_odi_values,
    ):
        win = Win.objects.get(id=uuid)
        if win == dh_win:
            assert win.total_expected_export_value == 0
            assert win.total_expected_non_export_value == 0
            assert win.total_expected_odi_value == 0
        else:
            assert win.total_expected_export_value == export_value
            assert win.total_expected_non_export_value == non_export_value
            assert win.total_expected_odi_value == odi_value

        versions = Version.objects.get_for_object(win).order_by('revision__date_created')
        assert versions.count() == 2
        comment = versions[0].revision.get_comment()
        assert comment == 'Legacy export wins totals migration - before.'
        comment = versions[1].revision.get_comment()
        assert comment == 'Legacy export wins totals migration - after.'

    assert 'Win matching query does not exist.' in caplog.text


def test_simulate(s3_stubber, caplog):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('ERROR')
    wins = WinFactory.create_batch(
        4,
        total_expected_export_value=0,
        total_expected_non_export_value=0,
        total_expected_odi_value=0,
        migrated_on=timezone.now(),
    )

    uuids = [win.id for win in wins]
    total_expected_export_values = [100, 200, 300, 400]
    total_expected_non_export_values = [200, 300, 400, 500]
    total_expected_odi_values = [10, 20, 30, 40]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_contents = ['id,total_expected_export_value,total_expected_non_export_value,'
                    'total_expected_odi_value']
    for uuid, export_value, non_export_value, odi_value in zip(
        uuids,
        total_expected_export_values,
        total_expected_non_export_values,
        total_expected_odi_values,
    ):
        csv_contents.append(f'{uuid},{export_value},{non_export_value},{odi_value}')

    csv_contents.append(f'{uuid4()},0,0,0,0')

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

    call_command('update_legacy_export_wins_totals', bucket, object_key, simulate=True)

    for uuid in uuids:
        win = Win.objects.get(id=uuid)
        assert win.total_expected_export_value == 0
        assert win.total_expected_non_export_value == 0
        assert win.total_expected_odi_value == 0

        versions = Version.objects.get_for_object(win).order_by('revision__date_created')
        assert versions.count() == 0

    assert 'Win matching query does not exist.' in caplog.text
