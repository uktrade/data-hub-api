import pytest

from datahub.company.test.factories import AdviserFactory
from datahub.export_win.constants import EXPORT_WINS_LEGACY_ID_START_VALUE
from datahub.export_win.models import (
    _calculate_totals_for_export_win,
    Breakdown,
    update_total_values,
    WinAdviser)
from datahub.export_win.test.factories import BreakdownFactory, WinAdviserFactory, WinFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def win_factory():
    return WinFactory()


@pytest.fixture
def adviser_factory():
    return AdviserFactory()


@pytest.fixture
def breakdown_factory(win_factory):
    return BreakdownFactory(win=win_factory)


class BaseLegacyModelTests:
    factory = None
    model_class = None

    def test_new_model_with_legacy_id_is_not_auto_incremented(self):
        model = self.factory(legacy_id=2233)
        model.save()

        loaded_model = self.model_class.objects.filter(id=model.id).first()
        assert loaded_model.legacy_id == model.legacy_id

    def test_edited_win_adviser_with_auto_incremented_legacy_id_not_auto_incremented_again(self):
        model = self.factory()
        model.save()
        model.save()

        loaded_model = self.model_class.objects.filter(id=model.id).first()
        assert loaded_model.legacy_id == EXPORT_WINS_LEGACY_ID_START_VALUE

    def test_new_model_with_no_legacy_id_is_auto_incremented(self):

        model = self.factory()
        model.save()

        loaded_model = self.model_class.objects.filter(id=model.id).first()
        assert loaded_model.legacy_id == EXPORT_WINS_LEGACY_ID_START_VALUE

    def test_new_model_with_no_legacy_id_are_auto_incremented(self):

        self.factory.create_batch(3)

        loaded_model = self.model_class.objects.all().order_by('legacy_id')
        for i, adviser in enumerate(loaded_model):
            assert adviser.legacy_id == EXPORT_WINS_LEGACY_ID_START_VALUE + i

    def test_new_model_with_no_legacy_id_after_migrated_model_is_auto_incremented(self):
        model1 = self.factory(legacy_id=654)
        model1.save()

        model2 = self.factory()
        model2.save()

        model3 = self.factory()
        model3.save()

        loaded_model1 = self.model_class.objects.filter(id=model1.id).first()
        assert loaded_model1.legacy_id == model1.legacy_id

        loaded_model2 = self.model_class.objects.filter(id=model2.id).first()
        assert loaded_model2.legacy_id == EXPORT_WINS_LEGACY_ID_START_VALUE

        loaded_mode3 = self.model_class.objects.filter(id=model3.id).first()
        assert loaded_mode3.legacy_id == EXPORT_WINS_LEGACY_ID_START_VALUE + 1


class TestWinAdviserModel(BaseLegacyModelTests):

    factory = WinAdviserFactory
    model_class = WinAdviser


class TestBreakdownModel(BaseLegacyModelTests):

    factory = BreakdownFactory
    model_class = Breakdown


def test_win_save(win_factory):
    win = win_factory
    calc_total = _calculate_totals_for_export_win(win)
    win.save()
    assert win.total_expected_export_value == calc_total['total_export_value']
    assert win.total_expected_non_export_value == calc_total['total_non_export_value']
    assert win.total_expected_odi_value == calc_total['total_odi_value']


def test_update_total_values(adviser_factory, win_factory, breakdown_factory):
    win = win_factory
    breakdown = breakdown_factory
    calc_total = _calculate_totals_for_export_win(win)
    expected_export_value = calc_total['total_export_value']
    expected_non_export_value = calc_total['total_non_export_value']
    expected_odi_value = calc_total['total_odi_value']
    update_total_values(sender=adviser_factory, instance=breakdown)
    win.refresh_from_db()
    assert win.total_expected_export_value == expected_export_value
    assert win.total_expected_non_export_value == expected_non_export_value
    assert win.total_expected_odi_value == expected_odi_value
