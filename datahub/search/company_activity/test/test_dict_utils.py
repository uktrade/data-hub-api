import pytest

from datahub.company_referral.test.factories import CompanyReferralFactory
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.search.company_activity import dict_utils

pytestmark = pytest.mark.django_db


def test_activity_interaction_dict():
    obj = None
    result = dict_utils.activity_interaction_dict(obj)
    assert result is None

    interaction = CompanyInteractionFactory()
    result = dict_utils.activity_interaction_dict(interaction)

    assert result['id'] == str(interaction.id)
    assert result['subject'] == interaction.subject
    assert result['dit_participants'][0]['adviser']['id'] == str(
        interaction.dit_participants.all()[0].adviser_id,
    )
    assert result['contacts'][0]['id'] == str(interaction.contacts.all()[0].id)
    assert result['communication_channel']['id'] == str(
        interaction.communication_channel.id,
    )
    assert result['service']['id'] == str(interaction.service.id)


def test_activity_referral_dict():
    obj = None
    result = dict_utils.activity_referral_dict(obj)
    assert result is None

    referral = CompanyReferralFactory()
    result = dict_utils.activity_referral_dict(referral)

    assert result['id'] == str(referral.id)
    assert result['notes'] == referral.notes
    assert result['recipient']['id'] == str(referral.recipient_id)
    assert result['contact']['id'] == str(referral.contact_id)
    assert result['created_by']['id'] == str(referral.created_by_id)


def test_activity_investment_dict():
    obj = None
    result = dict_utils.activity_investment_dict(obj)
    assert result is None

    investment = InvestmentProjectFactory()
    result = dict_utils.activity_investment_dict(investment)

    assert result['id'] == str(investment.id)
    assert result['created_by']['id'] == str(investment.created_by_id)
    assert result['investment_type']['id'] == str(
        investment.investment_type_id)
    assert result['estimated_land_date'] == investment.estimated_land_date
