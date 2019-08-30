import pytest
from elasticsearch.exceptions import NotFoundError

from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    InteractionDITParticipantFactory,
    InvestmentProjectInteractionFactory,
)
from datahub.search.interaction.apps import InteractionSearchApp

pytestmark = pytest.mark.django_db


def test_new_interaction_synced(setup_es):
    """Test that new interactions are synced to ES."""
    interaction = CompanyInteractionFactory()
    setup_es.indices.refresh()

    assert setup_es.get(
        index=InteractionSearchApp.es_model.get_write_index(),
        doc_type=InteractionSearchApp.name,
        id=interaction.pk,
    )


def test_updated_interaction_synced(setup_es):
    """Test that when an interaction is updated it is synced to ES."""
    interaction = CompanyInteractionFactory()
    new_subject = 'pluto'
    interaction.subject = new_subject
    interaction.save()
    setup_es.indices.refresh()

    result = setup_es.get(
        index=InteractionSearchApp.es_model.get_write_index(),
        doc_type=InteractionSearchApp.name,
        id=interaction.pk,
    )
    assert result['_source']['subject'] == new_subject


def test_deleted_interaction_deleted_from_es(setup_es):
    """
    Test that when an interaction is deleted from db it is also
    deleted from ES.
    """
    interaction = InvestmentProjectInteractionFactory()
    setup_es.indices.refresh()

    assert setup_es.get(
        index=InteractionSearchApp.es_model.get_write_index(),
        doc_type=InteractionSearchApp.name,
        id=interaction.pk,
    )

    interaction_id = interaction.pk
    interaction.delete()
    setup_es.indices.refresh()

    with pytest.raises(NotFoundError):
        assert setup_es.get(
            index=InteractionSearchApp.es_model.get_write_index(),
            doc_type=InteractionSearchApp.name,
            id=interaction_id,
        ) is None


def test_interaction_synced_when_dit_participant_added(setup_es):
    """Test that interactions are synced to ES if their DIT participants change."""
    interaction = CompanyInteractionFactory(dit_participants=[])
    setup_es.indices.refresh()

    doc = setup_es.get(
        index=InteractionSearchApp.es_model.get_read_alias(),
        doc_type=InteractionSearchApp.name,
        id=interaction.pk,
    )
    assert doc['_source']['dit_participants'] == []

    dit_participant = InteractionDITParticipantFactory(interaction=interaction)
    setup_es.indices.refresh()

    updated_doc = setup_es.get(
        index=InteractionSearchApp.es_model.get_read_alias(),
        doc_type=InteractionSearchApp.name,
        id=interaction.pk,
    )
    actual_dit_participants = updated_doc['_source']['dit_participants']
    assert len(actual_dit_participants) == 1
    assert actual_dit_participants[0]['adviser']['id'] == str(dit_participant.adviser.pk)
    assert actual_dit_participants[0]['team']['id'] == str(dit_participant.team.pk)


def test_updating_company_name_updates_interaction(setup_es):
    """Test that when a company name is updated, the company's interactions are synced to ES."""
    interaction = CompanyInteractionFactory()
    new_company_name = 'exogenous'
    interaction.company.name = new_company_name
    interaction.company.save()
    setup_es.indices.refresh()

    result = setup_es.get(
        index=InteractionSearchApp.es_model.get_write_index(),
        doc_type=InteractionSearchApp.name,
        id=interaction.pk,
    )
    assert result['_source']['company']['name'] == new_company_name


def test_updating_contact_name_updates_interaction(setup_es):
    """Test that when a contact's name is updated, the contact's interactions are synced to ES."""
    interaction = CompanyInteractionFactory()
    new_first_name = 'Jamie'
    new_last_name = 'Bloggs'
    contact = interaction.contacts.first()
    contact.first_name = new_first_name
    contact.last_name = new_last_name
    contact.save()
    setup_es.indices.refresh()

    result = setup_es.get(
        index=InteractionSearchApp.es_model.get_write_index(),
        doc_type=InteractionSearchApp.name,
        id=interaction.pk,
    )
    assert result['_source']['contacts'][0] == {
        'id': str(contact.pk),
        'first_name': new_first_name,
        'last_name': new_last_name,
        'name': f'{new_first_name} {new_last_name}',
    }


def test_updating_project_name_updates_interaction(setup_es):
    """
    Test that when an investment project's name is updated, the project's interactions are
    synced to ES.
    """
    interaction = InvestmentProjectInteractionFactory()
    new_project_name = 'helios'
    interaction.investment_project.name = new_project_name
    interaction.investment_project.save()
    setup_es.indices.refresh()

    result = setup_es.get(
        index=InteractionSearchApp.es_model.get_write_index(),
        doc_type=InteractionSearchApp.name,
        id=interaction.pk,
    )
    assert result['_source']['investment_project']['name'] == new_project_name
