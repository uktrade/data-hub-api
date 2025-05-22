from datetime import timedelta

import factory.fuzzy
from django.utils.timezone import now

from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.company_activity.models import CompanyActivity, KingsAwardRecipient, PromptPayments
from datahub.company_referral.test.factories import CompanyReferralFactory
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.investment_lead.test.factories import EYBLeadFactory
from datahub.metadata.test.factories import CountryFactory, SectorFactory
from datahub.omis.order.test.factories import OrderFactory


class CompanyActivityBaseFactory(factory.django.DjangoModelFactory):
    """The activity_source fields and the foriegn keys in the `CompanyActivity` model are
    automatically created as part of the save method inside the foreign key fields
    (oder, interaction, referral etc).
    """

    date = now()
    company = factory.SubFactory(CompanyFactory)
    activity_source = None

    class Meta:
        model = 'company_activity.CompanyActivity'


class CompanyActivityInteractionFactory(CompanyActivityBaseFactory):
    """Overwrite the _create to prevent the CompanyActivity from saving to the database.
    This is due to the Interaction already creating the CompanyActivity inside its
    model save.
    """

    activity_source = CompanyActivity.ActivitySource.interaction
    interaction = factory.SubFactory(CompanyInteractionFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Overwrite the _create to prevent the CompanyActivity from saving to the database.
        This is due to the Interaction already creating the CompanyActivity inside its
        model save.
        """
        obj = model_class(*args, **kwargs)
        return CompanyActivity.objects.get(interaction_id=obj.interaction_id)


class CompanyActivityReferralFactory(CompanyActivityBaseFactory):
    """CompanyActivity factory with a referral."""

    activity_source = CompanyActivity.ActivitySource.referral
    referral = factory.SubFactory(CompanyReferralFactory)

    class Meta:
        model = 'company_activity.CompanyActivity'

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Overwrite the _create to prevent the CompanyActivity from saving to the database.
        This is due to the CompanyReferral already creating the CompanyActivity inside its
        model save.
        """
        obj = model_class(*args, **kwargs)
        return CompanyActivity.objects.get(referral_id=obj.referral_id)


class CompanyActivityInvestmentProjectFactory(CompanyActivityBaseFactory):
    """CompanyActivity factory with an investment project."""

    activity_source = CompanyActivity.ActivitySource.investment
    investment = factory.SubFactory(InvestmentProjectFactory)

    class Meta:
        model = 'company_activity.CompanyActivity'

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Overwrite the _create to prevent the CompanyActivity from saving to the database.
        This is due to the InvestmentProject already creating the CompanyActivity inside its
        model save.
        """
        obj = model_class(*args, **kwargs)
        return CompanyActivity.objects.get(investment_id=obj.investment_id)


class CompanyActivityOmisOrderFactory(CompanyActivityBaseFactory):
    """CompanyActivity factory with an omis order."""

    activity_source = CompanyActivity.ActivitySource.order
    order = factory.SubFactory(OrderFactory)

    class Meta:
        model = 'company_activity.CompanyActivity'

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Overwrite the _create to prevent the CompanyActivity from saving to the database.
        This is due to the Omis Order already creating the CompanyActivity inside its
        model save.
        """
        obj = model_class(*args, **kwargs)
        return CompanyActivity.objects.get(order_id=obj.order_id)


class CompanyActivityIngestedFileFactory(factory.django.DjangoModelFactory):
    """CompanyActivity ingested file factory."""

    filepath = 'data-flow/exports/ExportGreatContactFormData/20240920T000000.jsonl.gz'
    file_created = now()

    class Meta:
        model = 'company_activity.IngestedFile'


class GreatExportEnquiryFactory(factory.django.DjangoModelFactory):
    """Ingested Great Export Enquiry data factory."""

    form_id = factory.Faker('pyint', min_value=0, max_value=999999)
    url = 'http://www.lewis.com/'
    form_created_at = now()
    submission_type = 'magna'
    submission_action = 'zendesk'
    company = factory.SubFactory(CompanyFactory)

    meta_sender_ip_address = ''
    meta_sender_country = factory.SubFactory(CountryFactory)
    meta_sender_email_address = 'dcarter@example.com'
    meta_subject = 'DPE Contact form - TEST PRODUCT'
    meta_full_name = 'TEST TEST'
    meta_subdomain = 'dit'
    meta_action_name = 'zendesk'
    meta_service_name = 'great'
    meta_spam_control = {}
    meta_email_address = 'meta@example.com'

    data_search = ''
    data_enquiry = factory.Faker('text')
    data_find_out_about = 'twitter'
    data_sector_primary = factory.SubFactory(SectorFactory)
    data_sector_primary_other = ''
    data_sector_secondary = factory.SubFactory(SectorFactory)
    data_sector_tertiary = factory.SubFactory(SectorFactory)
    data_triage_journey = ''
    data_received_support = True
    data_product_or_service_1 = 'TEST PRODUCT'
    data_product_or_service_2 = ''
    data_product_or_service_3 = ''
    data_product_or_service_4 = ''
    data_product_or_service_5 = ''
    data_about_your_experience = 'neverexported'
    data_contacted_gov_departments = True
    data_help_us_further = False
    data_help_us_improve = 'veryEasy'

    actor_type = 'Sender'
    actor_id = 1041
    actor_dit_email_address = 'crystalbrock@example.org'
    actor_dit_is_blacklisted = False
    actor_dit_is_whitelisted = False
    actor_dit_blacklisted_reason = None
    contact = factory.SubFactory(ContactFactory)

    @factory.post_generation
    def set_markets(self, create, extracted, **kwargs):
        # Do not create markets if we are only building the factory without
        # creating an instance in the DB.
        if not create:
            return

        self.data_markets.set([CountryFactory()])

    class Meta:
        model = 'company_activity.GreatExportEnquiry'


class CompanyActivityGreatExportEnquiryFactory(CompanyActivityBaseFactory):
    """CompanyActivity factory with an great export enquiry."""

    activity_source = CompanyActivity.ActivitySource.great_export_enquiry
    great_export_enquiry = factory.SubFactory(GreatExportEnquiryFactory)

    class Meta:
        model = 'company_activity.CompanyActivity'

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Overwrite the _create to prevent the CompanyActivity from saving to the database.
        This is due to the great export enquiry already creating the CompanyActivity inside its
        model save.
        """
        obj = model_class(*args, **kwargs)
        return CompanyActivity.objects.get(great_export_enquiry_id=obj.great_export_enquiry_id)


class CompanyActivityEYBLeadFactory(CompanyActivityBaseFactory):
    """CompanyActivity factory with an EYB lead."""

    activity_source = CompanyActivity.ActivitySource.eyb_lead
    eyb_lead = factory.SubFactory(EYBLeadFactory)

    class Meta:
        model = 'company_activity.CompanyActivity'

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Overwrite the _create to prevent the CompanyActivity from saving to the database.
        This is due to the EYB lead already creating the CompanyActivity inside its
        model save.
        """
        obj = model_class(*args, **kwargs)
        return CompanyActivity.objects.get(eyb_lead_id=obj.eyb_lead_id)


class StovaEventFactory(factory.django.DjangoModelFactory):
    """Ingested Stova Events data factory.
    The StoveEvent model save also creates a DataHub `Event`.
    """

    stova_event_id = factory.Faker('pyint', min_value=0, max_value=999999999)
    url = factory.Faker('uri_path')
    city = 'London, England'
    code = 'CodeTest'
    name = factory.Faker('first_name')
    state = 'London'
    country = 'UK'
    max_reg = 3
    end_date = now()
    timezone = 'Europe/London'
    folder_id = 987654321
    live_date = '2024-06-08T00:00:00+00:00'
    close_date = None
    created_by = 123458681
    price_type = 'net'
    start_date = now()
    description = factory.Faker('paragraph', nb_sentences=10)
    modified_by = 123458231
    contact_info = 'fake@fake.co.uk'
    created_date = '2024-05-10T08:06:53+00:00'
    location_city = 'London, England'
    location_name = 'Exhibition'
    modified_date = '2024-10-08T08:08:52+00:00'
    client_contact = 1239871
    location_state = 'Abu Dhabi'
    default_language = 'eng'
    location_country = 'United Arab Emirates'
    approval_required = False
    location_address1 = factory.Sequence(lambda x: f'{x} Fake Lane')
    location_address2 = factory.Sequence(lambda x: f'{x} Unreal Lane')
    location_address3 = factory.Sequence(lambda x: f'{x} Bing Lane')
    location_postcode = factory.Faker('postcode')
    standard_currency = 'Sterling'

    class Meta:
        model = 'company_activity.StovaEvent'


class StovaAttendeeFactory(factory.django.DjangoModelFactory):
    """Ingested Stova Attendee data factory."""

    stova_event_id = factory.Faker('pyint', min_value=0, max_value=999999999)
    stova_attendee_id = factory.Faker('pyint', min_value=0, max_value=999999999)

    created_by = 'John'
    created_date = now()
    modified_by = 'John'
    modified_date = now()

    email = 'john@test.com'
    first_name = 'John'
    last_name = 'Smith'
    attendee_questions = 'This is a question'

    company_name = 'A company name'
    category = 'A category'
    registration_status = 'The registration status'
    virtual_event_attendance = 'Virtual Event Attendance'
    language = 'English'
    last_lobby_login = now()
    company = factory.SubFactory(CompanyFactory)
    contact = factory.SubFactory(ContactFactory)
    ingested_stova_event = factory.SubFactory(StovaEventFactory)

    class Meta:
        model = 'company_activity.StovaAttendee'


class KingsAwardRecipientFactory(factory.django.DjangoModelFactory):
    """Ingested Kings Award recipient data factory."""

    company = factory.SubFactory(CompanyFactory)
    year_awarded = factory.fuzzy.FuzzyInteger(1966, now().year)
    category = factory.fuzzy.FuzzyChoice(KingsAwardRecipient.Category.values)
    citation = factory.Faker('paragraph')
    year_expired = factory.LazyAttribute(lambda x: x.year_awarded + 5)

    class Meta:
        model = KingsAwardRecipient


class PromptPaymentsFactory(factory.django.DjangoModelFactory):
    """Ingested Prompt Payments data factory."""

    source_id = factory.Sequence(lambda n: n)
    reporting_period_start_date = factory.Faker('date_object')
    reporting_period_end_date = factory.LazyAttribute(
        lambda o: o.reporting_period_start_date
        + timedelta(days=factory.fuzzy.FuzzyInteger(60, 90).fuzz()),
    )
    filing_date = factory.LazyAttribute(
        lambda o: o.reporting_period_end_date
        + timedelta(days=factory.fuzzy.FuzzyInteger(1, 30).fuzz()),
    )
    company_name = factory.Faker('company')
    company_house_number = factory.Faker('pystr_format', string_format='??######')
    company = factory.SubFactory(CompanyFactory)
    email_address = factory.Faker('email')
    contact = factory.SubFactory(ContactFactory)
    approved_by = factory.Faker('name')
    qualifying_contracts_in_period = factory.Faker('pybool')
    average_paid_days = factory.Faker('pyint', min_value=0, max_value=100)
    paid_within_30_days_pct = factory.Faker('pyint', min_value=0, max_value=100)
    paid_31_to_60_days_pct = factory.Faker('pyint', min_value=0, max_value=100)
    paid_after_61_days_pct = factory.Faker('pyint', min_value=0, max_value=100)
    paid_later_than_terms_pct = factory.Faker('pyint', min_value=0, max_value=100)
    payment_shortest_period_days = factory.Faker('pyint', min_value=0, max_value=30)
    payment_longest_period_days = factory.Faker('pyint', min_value=30, max_value=90)
    payment_max_period_days = factory.Faker('pyint', min_value=30, max_value=90)
    payment_terms_changed_comment = factory.Faker('sentence')
    payment_terms_changed_notified_comment = factory.Faker('sentence')
    code_of_practice = factory.Faker('word')
    other_electronic_invoicing = factory.Faker('pybool')
    other_supply_chain_finance = factory.Faker('pybool')
    other_retention_charges_in_policy = factory.Faker('pybool')
    other_retention_charges_in_past = factory.Faker('pybool')
    created_on = factory.LazyFunction(now)
    modified_on = factory.LazyFunction(now)

    class Meta:
        model = PromptPayments
