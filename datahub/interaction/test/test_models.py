import pytest
from django.conf import settings
from django.db.utils import IntegrityError

from datahub.company.test.factories import CompanyFactory
from datahub.company_activity.models import CompanyActivity
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
    """Tests Interaction export country model."""

    @pytest.mark.django_db
    def test_str(self):
        """Test the human friendly string representation of the object."""
        export_country = InteractionExportCountryFactory()
        status = f'{export_country.interaction} {export_country.country} {export_country.status}'
        assert str(export_country) == status

    @pytest.mark.django_db
    def test_unique_constraint(self):
        """Test unique constraint
        a interaction and country combination can't be added more than once.
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


@pytest.mark.django_db
class TestInteraction:
    """Tests for the Interaction model."""

    def test_save(self):
        """Test save also saves to the `CompanyActivity` model.
        Test save does not save to the `CompanyActivity` model if it already exists.
        """
        assert not CompanyActivity.objects.all().exists()
        interaction = CompanyInteractionFactory()
        assert CompanyActivity.objects.all().count() == 1

        company_activity = CompanyActivity.objects.get(interaction_id=interaction.id)
        assert company_activity.company_id == interaction.company_id
        assert company_activity.date == interaction.date
        assert company_activity.activity_source == CompanyActivity.ActivitySource.interaction

        # Update and save the interaction and ensure if doesn't create another
        # `CompanyActivity` and only updates it
        new_company = CompanyFactory()
        interaction.company_id = new_company.id
        interaction.save()

        assert CompanyActivity.objects.all().count() == 1
        company_activity.refresh_from_db()
        assert company_activity.company_id == new_company.id
