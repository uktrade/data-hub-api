import pytest
from django.contrib.admin import site

from datahub.company.test.factories import ContactFactory
from datahub.core.test_utils import AdminTestMixin
from datahub.interaction.admin import InteractionAdmin
from datahub.interaction.models import Interaction
from datahub.interaction.test.factories import CompanyInteractionFactory


class TestInteractionAdmin(AdminTestMixin):
    """Tests for interaction admin."""

    @pytest.mark.parametrize(
        'num_contacts,expected_display_value',
        (
            (0, ''),
            (1, '{first_contact_name}'),
            (2, '{first_contact_name} and 1 more'),
            (10, '{first_contact_name} and 9 more'),
        ),
    )
    def test_get_contact_names(self, num_contacts, expected_display_value):
        """Test that contact names are formatted as expected."""
        interaction = CompanyInteractionFactory(
            contacts=ContactFactory.create_batch(num_contacts),
        )
        interaction_admin = InteractionAdmin(Interaction, site)
        first_contact = interaction.contacts.order_by('pk').first()
        formatted_expected_display_value = expected_display_value.format(
            first_contact_name=first_contact.name if first_contact else '',
        )
        assert interaction_admin.get_contact_names(interaction) == formatted_expected_display_value
