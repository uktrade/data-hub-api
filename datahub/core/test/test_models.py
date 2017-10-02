import pytest
from dateutil.parser import parse as dateutil_parse

from .support.models import MyDisableableModel

pytestmark = pytest.mark.django_db


class TestDisableableModel:
    """Tests for the DisableableModel model."""

    def test_wasnt_disabled_if_disabled_on_is_none(self):
        """If disabled_on is None, return False."""
        date_on = dateutil_parse('2017-01-01 13:00:00')

        obj = MyDisableableModel(disabled_on=None)
        assert not obj.was_disabled_on(date_on)

    def test_was_disabled(self):
        """If disabled_on < date_on, return True."""
        disabled_on = dateutil_parse('2017-01-01 12:00:00')
        date_on = dateutil_parse('2017-01-01 13:00:00')

        obj = MyDisableableModel(disabled_on=disabled_on)
        assert obj.was_disabled_on(date_on)

    def test_wasnt_disabled(self):
        """If disabled_on > date_on, return False."""
        disabled_on = dateutil_parse('2017-01-01 14:00:00')
        date_on = dateutil_parse('2017-01-01 13:00:00')

        obj = MyDisableableModel(disabled_on=disabled_on)
        assert not obj.was_disabled_on(date_on)

    def test_can_be_disabled(self):
        """If is_disabled is True, disabled_on is set."""
        obj = MyDisableableModel(is_disabled=True)
        assert obj.disabled_on is not None
