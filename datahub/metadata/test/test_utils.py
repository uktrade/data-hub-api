import pytest

from datahub.metadata.models import Country
from datahub.metadata.test.factories import CountryFactory
from datahub.metadata.utils import get_country_by_country_name


@pytest.mark.django_db
class TestUtils:
    def test_get_country_by_country_name(self):
        country = CountryFactory(name='test country', iso_alpha2_code='ZZZZ')

        # Raises error when no country is found by name
        with pytest.raises(Country.DoesNotExist):
            get_country_by_country_name(name='dont find me')

        # Raises error when no country is found by name or iso
        with pytest.raises(Country.DoesNotExist):
            get_country_by_country_name(name='dont find me', default_iso='---')

        assert country.id == get_country_by_country_name(name='test country').id
        assert (
            country.id
            == get_country_by_country_name(
                name='no country with this name',
                default_iso='ZZZZ',
            ).id
        )
