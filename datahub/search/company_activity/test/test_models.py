from operator import attrgetter

import pytest

from datahub.company_activity.models import CompanyActivity as DBCompanyActivity
from datahub.company_activity.tests.factories import (
    CompanyActivityInteractionFactory,
    CompanyActivityInvestmentProjectFactory,
    CompanyActivityReferralFactory,
    CompanyActivityOmisOrderFactory,
)
from datahub.search.company_activity import CompanyActivitySearchApp
from datahub.search.company_activity.models import CompanyActivity

pytestmark = pytest.mark.django_db


def test_company_activity_referral_to_dict():
    """Test converting a CompanyActivity with a referral to a dict."""
    company_activity = CompanyActivityReferralFactory.build()

    result = CompanyActivity.db_object_to_dict(company_activity)

    assert result == {
        'interaction': company_activity.interaction,
        'investment': company_activity.investment,
        'order': company_activity.order,
        'referral': {
            'id': str(company_activity.referral_id),
            'completed_on': company_activity.referral.completed_on,
            'created_on': company_activity.referral.created_on,
            'subject': company_activity.referral.subject,
            'notes': company_activity.referral.notes,
            'status': company_activity.referral.status,
            'recipient': {
                'id': str(company_activity.referral.recipient_id),
                'first_name': company_activity.referral.recipient.first_name,
                'last_name': company_activity.referral.recipient.last_name,
                'name': company_activity.referral.recipient.name,
            },
            'created_by': {
                'id': str(company_activity.referral.created_by_id),
                'first_name': company_activity.referral.created_by.first_name,
                'last_name': company_activity.referral.created_by.last_name,
                'name': company_activity.referral.created_by.name,
            },
            'contact': {
                'id': str(company_activity.referral.contact_id),
                'first_name': company_activity.referral.contact.first_name,
                'last_name': company_activity.referral.contact.last_name,
                'name': company_activity.referral.contact.name,
            },
        },
        'company': (
            {
                'id': str(company_activity.company_id),
                'name': company_activity.company.name,
                'trading_names': company_activity.company.trading_names,
            }
            if company_activity.company
            else None
        ),
        'date': company_activity.date,
        'id': company_activity.pk,
        'activity_source': DBCompanyActivity.ActivitySource.referral,
        '_document_type': CompanyActivitySearchApp.name,
    }


def test_company_activity_interaction_to_dict():
    """Test converting a CompanyActivity with an interaction to a dict."""
    company_activity = CompanyActivityInteractionFactory.build()

    result = CompanyActivity.db_object_to_dict(company_activity)

    assert result == {
        'interaction': {
            'id': str(company_activity.interaction_id),
            'date': company_activity.interaction.date,
            'subject': company_activity.interaction.subject,
            'kind': company_activity.interaction.kind,
            'dit_participants': [
                {
                    'adviser': {
                        'id': str(dit_participant.adviser.pk),
                        'first_name': dit_participant.adviser.first_name,
                        'name': dit_participant.adviser.name,
                        'last_name': dit_participant.adviser.last_name,
                    },
                    'team': {
                        'id': str(dit_participant.team.pk),
                        'name': dit_participant.team.name,
                    },
                }
                for dit_participant in company_activity.interaction.dit_participants.order_by(
                    'adviser__pk',
                )
            ],
            'contacts': [
                {
                    'id': str(contact.pk),
                    'first_name': contact.first_name,
                    'name': contact.name,
                    'last_name': contact.last_name,
                }
                for contact in sorted(
                    company_activity.interaction.contacts.all(),
                    key=attrgetter('id'),
                )
            ],
            'communication_channel': {
                'id': str(company_activity.interaction.communication_channel.id),
                'name': company_activity.interaction.communication_channel.name,
            },
            'service': {
                'id': str(company_activity.interaction.service.id),
                'name': company_activity.interaction.service.name,
            },
        },
        'investment': company_activity.investment,
        'referral': company_activity.referral,
        'order': company_activity.order,
        'company': (
            {
                'id': str(company_activity.company_id),
                'name': company_activity.company.name,
                'trading_names': company_activity.company.trading_names,
            }
            if company_activity.company
            else None
        ),
        'activity_source': DBCompanyActivity.ActivitySource.interaction,
        'id': company_activity.pk,
        '_document_type': CompanyActivitySearchApp.name,
        'date': company_activity.date,
    }


def test_company_activity_investment_to_dict():
    """Test converting a CompanyActivity with an investment to a dict."""
    company_activity = CompanyActivityInvestmentProjectFactory.build()

    result = CompanyActivity.db_object_to_dict(company_activity)

    client_contacts = [
        {
            'id': contact.id,
            'name': contact.name,
            'first_name': contact.first_name,
            'last_name': contact.last_name,
        }
        for contact in company_activity.investment.client_contacts.all()
    ]

    assert result == {
        'interaction': company_activity.interaction,
        'order': company_activity.order,
        'investment': {
            'id': str(company_activity.investment.id),
            'name': company_activity.investment.name,
            'investment_type': {
                'id': str(company_activity.investment.investment_type.id),
                'name': company_activity.investment.investment_type.name,
            },
            'estimated_land_date': company_activity.investment.estimated_land_date,
            'total_investment': company_activity.investment.total_investment,
            'foreign_equity_investment': company_activity.investment.foreign_equity_investment,
            'gross_value_added': company_activity.investment.gross_value_added,
            'number_new_jobs': company_activity.investment.number_new_jobs,
            'created_by': {
                'id': str(company_activity.investment.created_by.id),
                'first_name': company_activity.investment.created_by.first_name,
                'last_name': company_activity.investment.created_by.last_name,
                'name': company_activity.investment.created_by.name,
            },
            'client_contacts': client_contacts,
        },
        'referral': company_activity.referral,
        'company': (
            {
                'id': str(company_activity.company_id),
                'name': company_activity.company.name,
                'trading_names': company_activity.company.trading_names,
            }
            if company_activity.company
            else None
        ),
        'activity_source': DBCompanyActivity.ActivitySource.investment,
        'id': company_activity.pk,
        '_document_type': CompanyActivitySearchApp.name,
        'date': company_activity.date,
    }


def test_company_activity_order_to_dict():
    """Test converting a CompanyActivity with an order to a dict."""
    company_activity = CompanyActivityOmisOrderFactory.build()

    result = CompanyActivity.db_object_to_dict(company_activity)

    assert result == {
        'interaction': company_activity.interaction,
        'investment': company_activity.investment,
        'referral': company_activity.referral,
        'company': (
            {
                'id': str(company_activity.company_id),
                'name': company_activity.company.name,
                'trading_names': company_activity.company.trading_names,
            }
            if company_activity.company
            else None
        ),
        'order': {
            'reference': company_activity.order.reference,
            'uk_region': {
                'id': str(company_activity.order.uk_region.id),
                'name': company_activity.order.uk_region.name,
            },
            'created_on': company_activity.order.created_on,
            'contact': {
                'name': company_activity.order.contact.name,
                'last_name': company_activity.order.contact.last_name,
                'id': str(company_activity.order.contact.id),
                'first_name': company_activity.order.contact.first_name,
                'job_title': company_activity.order.contact.job_title,
            },
            'id': str(company_activity.order.id),
            'created_by': {
                'name': company_activity.order.created_by.name,
                'last_name': company_activity.order.created_by.last_name,
                'id': str(company_activity.order.created_by.id),
                'first_name': company_activity.order.created_by.first_name,
            },
            'primary_market': {
                'name': company_activity.order.primary_market.name,
                'id': str(company_activity.order.primary_market.id),
            },
        },
        'activity_source': DBCompanyActivity.ActivitySource.order,
        'id': company_activity.pk,
        '_document_type': CompanyActivitySearchApp.name,
        'date': company_activity.date,
    }


def test_interactions_to_documents():
    """Test converting 2 CompanyActivity's to OpenSearch documents."""
    company_activities = CompanyActivityReferralFactory.build_batch(2)

    result = CompanyActivity.db_objects_to_documents(company_activities)

    assert {item['_id'] for item in result} == {item.pk for item in company_activities}
