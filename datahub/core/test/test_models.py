import pytest
from dateutil.parser import parse as dateutil_parse

from datahub.core.test.support.models import MyDisableableModel

pytestmark = pytest.mark.django_db


class TestDisableableModel:
    """Tests for the DisableableModel model."""

    def test_wasnt_disabled_if_disabled_on_is_none(self):
        """If disabled_on is None, return False."""
        date_on = dateutil_parse('2017-01-01T13:00:00Z')

        obj = MyDisableableModel(disabled_on=None)
        assert not obj.was_disabled_on(date_on)

    def test_was_disabled(self):
        """If disabled_on < date_on, return True."""
        disabled_on = dateutil_parse('2017-01-01T12:00:00Z')
        date_on = dateutil_parse('2017-01-01T13:00:00Z')

        obj = MyDisableableModel(disabled_on=disabled_on)
        assert obj.was_disabled_on(date_on)

    def test_wasnt_disabled(self):
        """If disabled_on > date_on, return False."""
        disabled_on = dateutil_parse('2017-01-01T14:00:00Z')
        date_on = dateutil_parse('2017-01-01T13:00:00Z')

        obj = MyDisableableModel(disabled_on=disabled_on)
        assert not obj.was_disabled_on(date_on)
