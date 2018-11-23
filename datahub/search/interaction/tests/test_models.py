import pytest

from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    InvestmentProjectInteractionFactory,
    ServiceDeliveryFactory,
)
from datahub.search.interaction.models import Interaction

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'factory_cls',
    (CompanyInteractionFactory, InvestmentProjectInteractionFactory),
)
def test_interaction_to_dict(setup_es, factory_cls):
    """Test converting an interaction to a dict."""
    interaction = factory_cls()
    result = Interaction.db_object_to_dict(interaction)

    assert result == {
        'id': interaction.pk,
        'kind': interaction.kind,
        'date': interaction.date,
        'company': {
            'id': str(interaction.company.pk),
            'name': interaction.company.name,
            'trading_name': interaction.company.alias,
        } if interaction.company else None,
        'company_sector': {
            'id': str(interaction.company.sector.pk),
            'name': interaction.company.sector.name,
            'ancestors': [{
                'id': str(ancestor.pk),
            } for ancestor in interaction.company.sector.get_ancestors()],
        } if interaction.company else None,
        'contact': {
            'id': str(interaction.contact.pk),
            'first_name': interaction.contact.first_name,
            'name': interaction.contact.name,
            'last_name': interaction.contact.last_name,
        },
        'is_event': interaction.is_event,
        'event': None,
        'service': {
            'id': str(interaction.service.pk),
            'name': interaction.service.name,
        },
        'subject': interaction.subject,
        'dit_adviser': {
            'id': str(interaction.dit_adviser.pk),
            'first_name': interaction.dit_adviser.first_name,
            'name': interaction.dit_adviser.name,
            'last_name': interaction.dit_adviser.last_name,
        },
        'notes': interaction.notes,
        'dit_team': {
            'id': str(interaction.dit_team.pk),
            'name': interaction.dit_team.name,
        },
        'communication_channel': {
            'id': str(interaction.communication_channel.pk),
            'name': interaction.communication_channel.name,
        },
        'investment_project': {
            'id': str(interaction.investment_project.pk),
            'name': interaction.investment_project.name,
        } if interaction.investment_project else None,
        'investment_project_sector': {
            'id': str(interaction.investment_project.sector.pk),
            'name': interaction.investment_project.sector.name,
            'ancestors': [{
                'id': str(ancestor.pk),
            } for ancestor in interaction.investment_project.sector.get_ancestors()],
        } if interaction.investment_project else None,
        'service_delivery_status': None,
        'grant_amount_offered': None,
        'net_company_receipt': None,
        'created_on': interaction.created_on,
        'modified_on': interaction.modified_on,
    }


def test_service_delivery_to_dict(setup_es):
    """Test converting an interaction to a dict."""
    interaction = ServiceDeliveryFactory()

    result = Interaction.db_object_to_dict(interaction)

    assert result == {
        'id': interaction.pk,
        'kind': interaction.kind,
        'date': interaction.date,
        'company': {
            'id': str(interaction.company.pk),
            'name': interaction.company.name,
            'trading_name': interaction.company.alias,
        },
        'company_sector': {
            'id': str(interaction.company.sector.pk),
            'name': interaction.company.sector.name,
            'ancestors': [{
                'id': str(ancestor.pk),
            } for ancestor in interaction.company.sector.get_ancestors()],
        },
        'contact': {
            'id': str(interaction.contact.pk),
            'first_name': interaction.contact.first_name,
            'name': interaction.contact.name,
            'last_name': interaction.contact.last_name,
        },
        'is_event': interaction.is_event,
        'event': None,
        'service': {
            'id': str(interaction.service.pk),
            'name': interaction.service.name,
        },
        'subject': interaction.subject,
        'dit_adviser': {
            'id': str(interaction.dit_adviser.pk),
            'first_name': interaction.dit_adviser.first_name,
            'name': interaction.dit_adviser.name,
            'last_name': interaction.dit_adviser.last_name,
        },
        'notes': interaction.notes,
        'dit_team': {
            'id': str(interaction.dit_team.pk),
            'name': interaction.dit_team.name,
        },
        'communication_channel': None,
        'investment_project': None,
        'investment_project_sector': None,
        'service_delivery_status': {
            'id': str(interaction.service_delivery_status.pk),
            'name': interaction.service_delivery_status.name,
        },
        'grant_amount_offered': interaction.grant_amount_offered,
        'net_company_receipt': interaction.net_company_receipt,
        'created_on': interaction.created_on,
        'modified_on': interaction.modified_on,
    }


def test_interactions_to_es_documents(setup_es):
    """Test converting 2 orders to Elasticsearch documents."""
    interactions = CompanyInteractionFactory.create_batch(2)

    result = Interaction.db_objects_to_es_documents(interactions)

    assert {item['_id'] for item in result} == {item.pk for item in interactions}
