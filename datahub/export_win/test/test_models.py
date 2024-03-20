import pytest

from datahub.export_win.constants import EXPORT_WINS_LEGACY_ID_START_VALUE
from datahub.export_win.models import Breakdown, WinAdviser
from datahub.export_win.test.factories import BreakdownFactory, WinAdviserFactory


pytestmark = pytest.mark.django_db


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
