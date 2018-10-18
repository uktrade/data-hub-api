import pytest
from django.conf import settings

from datahub.interaction.test.factories import CompanyInteractionFactory


@pytest.mark.django_db
def test_interaction_get_absolute_url():
    """Test that Interaction.get_absolute_url() returns the correct URL."""
    interaction = CompanyInteractionFactory.build()
    assert interaction.get_absolute_url() == (
        f'{settings.DATAHUB_FRONTEND_URL_PREFIXES["interaction"]}/{interaction.pk}'
    )
