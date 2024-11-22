from datetime import date

import pytest
from opensearchpy.exceptions import NotFoundError

from datahub.company.test.factories import (
    AdviserFactory,
    ContactFactory,
)
from datahub.company_activity.models import CompanyActivity as DBCompanyActivity
from datahub.company_activity.tests.factories import (
    CompanyActivityInteractionFactory,
    GreatExportEnquiryFactory,
)
from datahub.company_referral.test.factories import CompanyReferralFactory
from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    InteractionDITParticipantFactory,
)
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.investment_lead.test.factories import EYBLeadFactory
from datahub.omis.order.test.factories import OrderFactory
from datahub.search.company_activity.apps import CompanyActivitySearchApp

pytestmark = pytest.mark.django_db


def test_new_company_activities_synced(opensearch_with_signals):
    """Test that new company activities are synced to OpenSearch."""
    company_activity = CompanyActivityInteractionFactory()
    opensearch_with_signals.indices.refresh()

    assert opensearch_with_signals.get(
        index=CompanyActivitySearchApp.search_model.get_write_index(),
        id=company_activity.pk,
    )


def test_updated_company_activity_synced(opensearch_with_signals):
    """Test that when a company activity is updated it is synced to OpenSearch."""
    company_activity = CompanyActivityInteractionFactory()
    new_activity_source = 'new_source'
    company_activity.activity_source = new_activity_source
    company_activity.save()
    opensearch_with_signals.indices.refresh()

    result = opensearch_with_signals.get(
        index=CompanyActivitySearchApp.search_model.get_write_index(),
        id=company_activity.pk,
    )
    assert result['_source']['activity_source'] == new_activity_source


def test_deleted_company_activity_is_deleted_from_opensearch(opensearch_with_signals):
    """
    Test that when a company activity is deleted from db it is also
    deleted from OpenSearch.
    """
    company_activity = CompanyActivityInteractionFactory()
    opensearch_with_signals.indices.refresh()

    assert opensearch_with_signals.get(
        index=CompanyActivitySearchApp.search_model.get_write_index(),
        id=company_activity.pk,
    )

    company_activity_id = company_activity.pk
    company_activity.delete()
    opensearch_with_signals.indices.refresh()

    with pytest.raises(NotFoundError):
        assert (
            opensearch_with_signals.get(
                index=CompanyActivitySearchApp.search_model.get_write_index(),
                id=company_activity_id,
            )
            is None
        )


def test_company_activity_syncs_interaction_fields_when_changed(opensearch_with_signals):
    """Test that company_activities are synced to OpenSearch if their interactions updates."""
    interaction = CompanyInteractionFactory(dit_participants=[], contacts=[])
    company_activity = DBCompanyActivity.objects.get(interaction_id=interaction.id)
    opensearch_with_signals.indices.refresh()

    doc = opensearch_with_signals.get(
        index=CompanyActivitySearchApp.search_model.get_read_alias(),
        id=company_activity.pk,
    )
    assert doc['_source']['interaction']['dit_participants'] == []
    assert doc['_source']['interaction']['contacts'] == []

    dit_participant = InteractionDITParticipantFactory(interaction=interaction)
    contact = ContactFactory()
    interaction.contacts.add(contact)
    interaction.save()

    opensearch_with_signals.indices.refresh()

    updated_doc = opensearch_with_signals.get(
        index=CompanyActivitySearchApp.search_model.get_read_alias(),
        id=company_activity.pk,
    )
    actual_dit_participants = updated_doc['_source']['interaction']['dit_participants']
    assert len(actual_dit_participants) == 1
    assert actual_dit_participants[0]['adviser']['id'] == str(dit_participant.adviser.pk)
    assert actual_dit_participants[0]['team']['id'] == str(dit_participant.team.pk)

    actual_contacts = updated_doc['_source']['interaction']['contacts']
    assert len(actual_contacts) == 1
    assert actual_contacts[0]['id'] == str(contact.id)
    assert actual_contacts[0]['name'] == contact.name


def test_updating_company_name_updates_activity(opensearch_with_signals):
    """
    Test that when a company name is updated, the company activity company name is synced to
    OpenSearch.
    """
    interaction = CompanyInteractionFactory(dit_participants=[], contacts=[])
    company_activity = DBCompanyActivity.objects.get(interaction_id=interaction.id)
    new_company_name = 'exogenous'
    company_activity.company.name = new_company_name
    company_activity.company.save()

    opensearch_with_signals.indices.refresh()

    result = opensearch_with_signals.get(
        index=CompanyActivitySearchApp.search_model.get_write_index(),
        id=company_activity.pk,
    )
    assert result['_source']['company']['name'] == new_company_name


def test_company_activity_syncs_referral_fields_when_changed(opensearch_with_signals):
    """Test that company_activities are synced to OpenSearch if their referrals updates."""
    referral = CompanyReferralFactory()
    company_activity = DBCompanyActivity.objects.get(referral_id=referral.id)
    opensearch_with_signals.indices.refresh()

    doc = opensearch_with_signals.get(
        index=CompanyActivitySearchApp.search_model.get_read_alias(),
        id=company_activity.pk,
    )

    assert doc['_source']['referral']['recipient']['id'] == str(referral.recipient_id)
    assert doc['_source']['referral']['contact']['id'] == str(referral.contact_id)
    assert doc['_source']['referral']['created_by']['id'] == str(referral.created_by_id)
    assert doc['_source']['referral']['subject'] == referral.subject

    new_recipient = AdviserFactory()
    referral.recipient = new_recipient
    new_contact = ContactFactory()
    referral.contact = new_contact
    new_created_by = AdviserFactory()
    referral.created_by = new_created_by
    new_subject = 'new subject'
    referral.subject = new_subject

    referral.save()

    opensearch_with_signals.indices.refresh()

    updated_doc = opensearch_with_signals.get(
        index=CompanyActivitySearchApp.search_model.get_read_alias(),
        id=company_activity.pk,
    )
    actual_referral = updated_doc['_source']['referral']
    assert actual_referral['recipient']['id'] == str(new_recipient.id)
    assert actual_referral['contact']['id'] == str(new_contact.id)
    assert actual_referral['created_by']['id'] == str(new_created_by.id)
    assert actual_referral['subject'] == new_subject


def test_company_activity_syncs_investment_fields_when_changed(opensearch_with_signals):
    """Test that company_activities are synced to OpenSearch if their investment updates."""
    investment = InvestmentProjectFactory()
    company_activity = DBCompanyActivity.objects.get(investment_id=investment.id)
    opensearch_with_signals.indices.refresh()

    doc = opensearch_with_signals.get(
        index=CompanyActivitySearchApp.search_model.get_read_alias(),
        id=company_activity.pk,
    )

    assert doc['_source']['investment']['estimated_land_date'] == str(
        investment.estimated_land_date,
    )
    assert doc['_source']['investment']['created_by']['id'] == str(investment.created_by_id)

    new_estimated_land_date = date(2023, 10, 12)
    investment.estimated_land_date = new_estimated_land_date

    new_created_by = AdviserFactory()
    investment.created_by = new_created_by

    investment.save()

    opensearch_with_signals.indices.refresh()

    updated_doc = opensearch_with_signals.get(
        index=CompanyActivitySearchApp.search_model.get_read_alias(),
        id=company_activity.pk,
    )
    actual_investment = updated_doc['_source']['investment']
    assert actual_investment['estimated_land_date'] == str(new_estimated_land_date)
    assert actual_investment['created_by']['id'] == str(new_created_by.id)


def test_company_activity_syncs_order_fields_when_changed(opensearch_with_signals):
    """Test that company_activities are synced to OpenSearch if their omis order updates."""
    order = OrderFactory()
    company_activity = DBCompanyActivity.objects.get(order_id=order.id)
    opensearch_with_signals.indices.refresh()

    doc = opensearch_with_signals.get(
        index=CompanyActivitySearchApp.search_model.get_read_alias(),
        id=company_activity.pk,
    )

    assert doc['_source']['order']['contact']['id'] == str(order.contact_id)
    assert doc['_source']['order']['created_by']['id'] == str(order.created_by_id)
    new_contact = ContactFactory()
    order.contact = new_contact

    new_created_by = AdviserFactory()
    order.created_by = new_created_by
    order.save()

    opensearch_with_signals.indices.refresh()

    updated_doc = opensearch_with_signals.get(
        index=CompanyActivitySearchApp.search_model.get_read_alias(),
        id=company_activity.pk,
    )
    actual_order = updated_doc['_source']['order']
    assert actual_order['contact']['id'] == str(new_contact.id)
    assert actual_order['created_by']['id'] == str(new_created_by.id)


def test_company_activity_syncs_great_fields_when_changed(opensearch_with_signals):
    """
    Test that company_activities are synced to OpenSearch
    if their great export enquiry order updates.
    """
    great_export_enquiry = GreatExportEnquiryFactory()
    company_activity = DBCompanyActivity.objects.get(
        great_export_enquiry_id=great_export_enquiry.id,
    )
    opensearch_with_signals.indices.refresh()

    doc = opensearch_with_signals.get(
        index=CompanyActivitySearchApp.search_model.get_read_alias(),
        id=company_activity.pk,
    )

    assert doc['_source']['great_export_enquiry']['contact']['id'] == str(
        great_export_enquiry.contact_id,
    )
    assert (
        doc['_source']['great_export_enquiry']['meta_email_address']
        == great_export_enquiry.meta_email_address
    )
    assert (
        doc['_source']['great_export_enquiry']['meta_subject'] == great_export_enquiry.meta_subject
    )

    new_contact = ContactFactory()
    great_export_enquiry.contact = new_contact

    new_email_address = 'fake@fake.com'
    great_export_enquiry.meta_email_address = new_email_address

    new_subject = 'great subject'

    great_export_enquiry.meta_subject = new_subject

    great_export_enquiry.save()

    opensearch_with_signals.indices.refresh()

    updated_doc = opensearch_with_signals.get(
        index=CompanyActivitySearchApp.search_model.get_read_alias(),
        id=company_activity.pk,
    )
    actual_great_export_enquiry = updated_doc['_source']['great_export_enquiry']
    assert actual_great_export_enquiry['contact']['id'] == str(new_contact.id)
    assert actual_great_export_enquiry['meta_email_address'] == new_email_address
    assert actual_great_export_enquiry['meta_subject'] == new_subject


def test_company_activity_syncs_eyb_lead_fields_when_changed(opensearch_with_signals):
    """Test that company_activities are synced to OpenSearch if their eyb lead updates."""
    eyb_lead = EYBLeadFactory()
    company_activity = DBCompanyActivity.objects.get(eyb_lead=eyb_lead)
    opensearch_with_signals.indices.refresh()

    doc = opensearch_with_signals.get(
        index=CompanyActivitySearchApp.search_model.get_read_alias(),
        id=company_activity.pk,
    )

    assert doc['_source']['eyb_lead']['duns_number'] == str(eyb_lead.duns_number)
    assert doc['_source']['eyb_lead']['company_name'] == str(eyb_lead.company_name)
    new_company_name = str(eyb_lead.company_name) + ' new'
    eyb_lead.company_name = new_company_name

    eyb_lead.save()

    opensearch_with_signals.indices.refresh()

    updated_doc = opensearch_with_signals.get(
        index=CompanyActivitySearchApp.search_model.get_read_alias(),
        id=company_activity.pk,
    )
    actual_eyb_lead = updated_doc['_source']['eyb_lead']
    assert actual_eyb_lead['duns_number'] == str(eyb_lead.duns_number)
    assert actual_eyb_lead['company_name'] == str(new_company_name)
