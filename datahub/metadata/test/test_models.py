import pytest
from dateutil.parser import parse as dateutil_parse

from ..models import Country


pytestmark = pytest.mark.django_db


class TestCountry:
    """Tests for the Country model."""

    def test_wasnt_omis_disabled_if_omis_disabled_on_is_none(self):
        """If omis_disabled_on is None, return False."""
        date_on = dateutil_parse('2017-01-01 13:00:00')

        country = Country(omis_disabled_on=None)
        assert not country.was_omis_disabled_on(date_on)

    def test_was_omis_disabled(self):
        """If omis_disabled_on < date_on, return True."""
        omis_disabled_on = dateutil_parse('2017-01-01 12:00:00')
        date_on = dateutil_parse('2017-01-01 13:00:00')

        country = Country(omis_disabled_on=omis_disabled_on)
        assert country.was_omis_disabled_on(date_on)

    def test_wasnt_omis_disabled(self):
        """If omis_disabled_on > date_on, return False."""
        omis_disabled_on = dateutil_parse('2017-01-01 14:00:00')
        date_on = dateutil_parse('2017-01-01 13:00:00')

        country = Country(omis_disabled_on=omis_disabled_on)
        assert not country.was_omis_disabled_on(date_on)
