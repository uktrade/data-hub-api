import pytest
import pytz

from datahub.company_activity.tests.factories import GreatExportEnquiryFactory
from datahub.company_referral.test.factories import CompanyReferralFactory
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.investment_lead.test.factories import EYBLeadFactory
from datahub.omis.order.test.factories import OrderFactory
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
    assert result['eyb_leads'] == []


def assert_eyb_lead_in_result_list(eyb_lead, result_list):
    assert {
        'id': str(eyb_lead.id),
        'company_name': eyb_lead.company_name,
        'created_on': eyb_lead.created_on,
        'triage_created': eyb_lead.triage_created.replace(tzinfo=pytz.UTC),
        'is_high_value': eyb_lead.is_high_value,
    } in result_list


def test_activity_investment_with_eyb_leads_dict():
    obj = None
    result = dict_utils.activity_investment_dict(obj)
    assert result is None

    investment = InvestmentProjectFactory()
    eyb_leads_is_high_value = EYBLeadFactory(
        investment_projects=[investment.id],
        is_high_value=True,
    )
    eyb_leads_is_not_high_value = EYBLeadFactory(
        investment_projects=[investment.id],
        is_high_value=False,
    )
    result = dict_utils.activity_investment_dict(investment)

    assert result['id'] == str(investment.id)
    assert result['created_by']['id'] == str(investment.created_by_id)
    assert result['investment_type']['id'] == str(
        investment.investment_type_id)
    assert result['estimated_land_date'] == investment.estimated_land_date
    assert_eyb_lead_in_result_list(eyb_leads_is_high_value, result['eyb_leads'])
    assert_eyb_lead_in_result_list(eyb_leads_is_not_high_value, result['eyb_leads'])


def test_activity_order_dict():
    obj = None
    result = dict_utils.activity_order_dict(obj)
    assert result is None

    order = OrderFactory()
    result = dict_utils.activity_order_dict(order)

    assert result['id'] == str(order.id)
    assert result['created_by']['id'] == str(order.created_by_id)
    assert result['contact']['id'] == str(order.contact_id)
    assert result['primary_market']['id'] == order.primary_market_id


def test_activity_great_dict():
    obj = None
    result = dict_utils.activity_great_dict(obj)
    assert result is None

    great = GreatExportEnquiryFactory()
    result = dict_utils.activity_great_dict(great)

    assert result['id'] == str(great.id)
    assert result['form_created_at'] == great.form_created_at
    assert result['meta_full_name'] == great.meta_full_name
    assert result['meta_email_address'] == great.meta_email_address
    assert result['contact']['id'] == str(great.contact.id)
    assert result['meta_subject'] == great.meta_subject
    assert result['data_enquiry'] == great.data_enquiry


def test_activity_eyb_lead_dict():
    obj = None
    result = dict_utils.activity_eyb_lead_dict(obj)
    assert result is None

    eyb_lead = EYBLeadFactory()
    result = dict_utils.activity_eyb_lead_dict(eyb_lead)

    assert result['id'] == str(eyb_lead.id)
    assert result['created_on'] == eyb_lead.created_on
    assert result['duns_number'] == eyb_lead.duns_number
    assert result['company_name'] == eyb_lead.company_name
