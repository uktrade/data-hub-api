from importlib import import_module

import pytest
from django.apps import apps

from datahub.export_win.constants import EXPORT_WINS_LEGACY_ID_START_VALUE
from datahub.export_win.test.factories import BreakdownFactory, WinAdviserFactory

pytestmark = pytest.mark.django_db


class TestLegacyIdMigrations():

    @pytest.mark.parametrize(
        'factory,model',
        (
            (
                WinAdviserFactory,
                'WinAdviser',
            ),
            (
                BreakdownFactory,
                'Breakdown',
            ),
        ),
    )
    def test_legacy_id_forwards_func(self, factory, model):
        module = import_module('datahub.export_win.legacy_id_utils')

        new_adviser = factory()

        module.forwards_func(apps, None, model)
        assert new_adviser.legacy_id == EXPORT_WINS_LEGACY_ID_START_VALUE
