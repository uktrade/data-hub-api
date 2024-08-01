import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.interaction.test.factories import AdviserFactory
from datahub.interaction.test.factories import CompaniesInteractionFactory
from datahub.interaction.test.factories import InteractionDITParticipantFactory

pytestmark = pytest.mark.django_db


def test_run__fake_uuids(caplog):
    """
    Test that the command:

    - ignores rows with unmatched adviser UUIDs
    """
    caplog.set_level('INFO')

    fake_old_adviser_uuid = '00000000-1234-0000-0000-000000000000'
    fake_new_adviser_uuid = '00000000-4321-4321-0000-000000000000'

    call_command(
        'update_interactions_to_new_adviser',
        fake_old_adviser_uuid,
        fake_new_adviser_uuid,
    )

    assert 'No interactions to update.' in caplog.text


@pytest.mark.parametrize(
    'simulate',
    (
        (True),
        (False),
    ),
)
def test_run__update_interaction_participant(simulate):
    """
    Test that the command:
    - updates records only if simulate=False is passed
    - does not update records if simulate=True is passed
    - updates interaction participants to new adviser
    """
    participant_interaction = InteractionDITParticipantFactory()
    new_adviser = AdviserFactory()

    if simulate:
        call_command(
            'update_interactions_to_new_adviser',
            participant_interaction.adviser_id,
            new_adviser.id,
            '--simulate',
        )
    else:
        call_command(
            'update_interactions_to_new_adviser',
            participant_interaction.adviser_id,
            new_adviser.id,
        )

    participant_interaction.refresh_from_db()

    if simulate:
        # No changes expected
        assert participant_interaction.adviser_id == participant_interaction.adviser_id
    else:
        # Change expected
        assert participant_interaction.adviser_id == new_adviser.id


def test_run__no_update_for_advisers_with_same_interaction(caplog):
    """
    Test that the command:

    - does not update advisers which have the same interaction as this breaks
        the unique_together constraint.
    """
    caplog.set_level('INFO')

    # Old adviser with same interaction id as new adviser
    same_interaction = CompaniesInteractionFactory()
    old_adviser = AdviserFactory()
    interaction_with_old_adviser = InteractionDITParticipantFactory(
        adviser=old_adviser, interaction=same_interaction,
    )
    new_adviser = AdviserFactory()
    interaction_with_new_adviser = InteractionDITParticipantFactory(
        adviser=new_adviser, interaction=same_interaction,
    )

    call_command('update_interactions_to_new_adviser', old_adviser.id, new_adviser.id)

    interaction_with_old_adviser.refresh_from_db()
    interaction_with_new_adviser.refresh_from_db()

    # No changes expected as would fail unique constraint
    assert 'No interactions to update.' in caplog.text
    assert (
        interaction_with_new_adviser.adviser_id
        == interaction_with_new_adviser.adviser_id
    )
    assert (
        interaction_with_old_adviser.adviser_id
        == interaction_with_old_adviser.adviser_id
    )


def test_audit_log():
    """Test that reversion revisions are created."""
    interaction_participant = InteractionDITParticipantFactory.create_batch(2)
    adviser = AdviserFactory()

    interaction_participant_1 = interaction_participant[0]
    interaction_participant_2 = interaction_participant[1]

    call_command(
        'update_interactions_to_new_adviser',
        interaction_participant_2.adviser_id,
        adviser.id,
    )

    versions = Version.objects.get_for_object(interaction_participant_1)
    assert versions.count() == 0

    versions = Version.objects.get_for_object(interaction_participant_2)
    assert versions.count() == 1
    assert (
        versions[0].revision.get_comment()
        == f'Updated interactions: 1 to have new adviser id {adviser.id}'
    )
