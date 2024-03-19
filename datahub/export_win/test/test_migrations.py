from importlib import import_module

import pytest

from django.apps import apps

from datahub.export_win.constants import EXPORT_WINS_LEGACY_ID_START_VALUE
from datahub.export_win.test.factories import WinAdviserFactory


pytestmark = pytest.mark.django_db


class TestWinAdviserMigrations():
    def test_legacy_id_forwards_func(self):
        module = import_module('datahub.export_win.migrations.0030_winadviser_legacy_id')

        new_adviser = WinAdviserFactory()

        module.forwards_func(apps, None)
        assert new_adviser.legacy_id == EXPORT_WINS_LEGACY_ID_START_VALUE
