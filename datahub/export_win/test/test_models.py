import pytest

from datahub.export_win.constants import EXPORT_WINS_LEGACY_ID_START_VALUE
from datahub.export_win.models import WinAdviser
from datahub.export_win.test.factories import WinAdviserFactory


pytestmark = pytest.mark.django_db


class TestWinAdviserModel:
    def test_new_win_adviser_with_legacy_id_is_not_auto_incremented(self):
        win_adviser = WinAdviserFactory(legacy_id=2233)
        win_adviser.save()

        load_adviser = WinAdviser.objects.filter(id=win_adviser.id).first()
        assert load_adviser.legacy_id == win_adviser.legacy_id

    def test_edited_win_adviser_with_auto_incremented_legacy_id_not_auto_incremented_again(self):
        win_adviser = WinAdviserFactory()
        win_adviser.save()
        win_adviser.location = 'UPDATED'
        win_adviser.save()

        load_adviser = WinAdviser.objects.filter(id=win_adviser.id).first()
        assert load_adviser.legacy_id == EXPORT_WINS_LEGACY_ID_START_VALUE

    def test_new_win_adviser_with_no_legacy_id_is_auto_incremented(self):

        win_adviser = WinAdviserFactory()
        win_adviser.save()

        load_adviser = WinAdviser.objects.filter(id=win_adviser.id).first()
        assert load_adviser.legacy_id == EXPORT_WINS_LEGACY_ID_START_VALUE

    def test_new_win_advisers_with_no_legacy_id_are_auto_incremented(self):

        WinAdviserFactory.create_batch(3)

        loaded_advisers = WinAdviser.objects.all().order_by('legacy_id')
        for i, adviser in enumerate(loaded_advisers):
            assert adviser.legacy_id == EXPORT_WINS_LEGACY_ID_START_VALUE + i

    def test_new_win_adviser_with_no_legacy_id_after_migrated_adviser_is_auto_incremented(self):
        win_adviser1 = WinAdviserFactory(legacy_id=654)
        win_adviser1.save()

        win_adviser2 = WinAdviserFactory()
        win_adviser2.save()

        win_adviser3 = WinAdviserFactory()
        win_adviser3.save()

        load_adviser1 = WinAdviser.objects.filter(id=win_adviser1.id).first()
        assert load_adviser1.legacy_id == win_adviser1.legacy_id

        load_adviser2 = WinAdviser.objects.filter(id=win_adviser2.id).first()
        assert load_adviser2.legacy_id == EXPORT_WINS_LEGACY_ID_START_VALUE

        load_adviser3 = WinAdviser.objects.filter(id=win_adviser3.id).first()
        assert load_adviser3.legacy_id == EXPORT_WINS_LEGACY_ID_START_VALUE + 1
