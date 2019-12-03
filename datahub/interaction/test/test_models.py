import pytest
from django.conf import settings
from django.db.utils import IntegrityError

from datahub.core.test_utils import random_obj_for_model
from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    InteractionExportCountryFactory,
)
from datahub.metadata.models import Country


@pytest.mark.django_db
def test_interaction_get_absolute_url():
    """Test that Interaction.get_absolute_url() returns the correct URL."""
    interaction = CompanyInteractionFactory.build()
    assert interaction.get_absolute_url() == (
        f'{settings.DATAHUB_FRONTEND_URL_PREFIXES["interaction"]}/{interaction.pk}'
    )


class TestInteractionExportCountry:
    """Tests Interaction export country model"""

    @pytest.mark.django_db
    def test_str(self):
        """Test the human friendly string representation of the object"""
        export_country = InteractionExportCountryFactory()
        status = f'{export_country.interaction} {export_country.country} {export_country.status}'
        assert str(export_country) == status

    @pytest.mark.django_db
    def test_unique_constraint(self):
        """
        Test unique constraint
        a interaction and country combination can't be added more than once
        """
        interaction = CompanyInteractionFactory()
        country = random_obj_for_model(Country)

        InteractionExportCountryFactory(
            interaction=interaction,
            country=country,
        )

        with pytest.raises(IntegrityError):
            InteractionExportCountryFactory(
                interaction=interaction,
                country=country,
            )
