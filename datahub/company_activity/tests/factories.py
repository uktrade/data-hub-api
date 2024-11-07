import factory.fuzzy
from django.utils.timezone import now

from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.company_activity.models import CompanyActivity
from datahub.company_referral.test.factories import CompanyReferralFactory
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.metadata.test.factories import CountryFactory, SectorFactory
from datahub.omis.order.test.factories import OrderFactory


class CompanyActivityBaseFactory(factory.django.DjangoModelFactory):
    """
    The activity_source fields and the foriegn keys in the `CompanyActivity` model are
    automatically created as part of the save method inside the foreign key fields
    (oder, interaction, referral etc).
    """

    date = now()
    company = factory.SubFactory(CompanyFactory)
    activity_source = None

    class Meta:
        model = 'company_activity.CompanyActivity'


class CompanyActivityInteractionFactory(CompanyActivityBaseFactory):
    """
    Overwrite the _create to prevent the CompanyActivity from saving to the database.
    This is due to the Interaction already creating the CompanyActivity inside its
    model save.
    """

    activity_source = CompanyActivity.ActivitySource.interaction
    interaction = factory.SubFactory(CompanyInteractionFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """
        Overwrite the _create to prevent the CompanyActivity from saving to the database.
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
        """
        Overwrite the _create to prevent the CompanyActivity from saving to the database.
        This is due to the CompanyReferral already creating the CompanyActivity inside its
        model save.
        """
        obj = model_class(*args, **kwargs)
        return CompanyActivity.objects.get(referral_id=obj.referral_id)


class CompanyActivityInvestmentProjectFactory(CompanyActivityBaseFactory):
    """
    CompanyActivity factory with an investment project.
    """

    activity_source = CompanyActivity.ActivitySource.investment
    investment = factory.SubFactory(InvestmentProjectFactory)

    class Meta:
        model = 'company_activity.CompanyActivity'

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """
        Overwrite the _create to prevent the CompanyActivity from saving to the database.
        This is due to the InvestmentProject already creating the CompanyActivity inside its
        model save.
        """
        obj = model_class(*args, **kwargs)
        return CompanyActivity.objects.get(investment_id=obj.investment_id)


class CompanyActivityOmisOrderFactory(CompanyActivityBaseFactory):
    """
    CompanyActivity factory with an omis order.
    """

    activity_source = CompanyActivity.ActivitySource.order
    order = factory.SubFactory(OrderFactory)

    class Meta:
        model = 'company_activity.CompanyActivity'

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """
        Overwrite the _create to prevent the CompanyActivity from saving to the database.
        This is due to the Omis Order already creating the CompanyActivity inside its
        model save.
        """
        obj = model_class(*args, **kwargs)
        return CompanyActivity.objects.get(order_id=obj.order_id)


class CompanyActivityIngestedFileFactory(factory.django.DjangoModelFactory):
    """
    CompanyActivity ingested file factory
    """

    filepath = 'data-flow/exports/ExportGreatContactFormData/20240920T000000.jsonl.gz'
    created_on = now()

    class Meta:
        model = 'company_activity.IngestedFile'

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        """If specified, override the created_on field.

        Because the `created_on` field has `auto_now_add=True`, Django overrides
        any provided value with `now()`; and this happens "after" factory_boy's code
        runs. To properly override it, we need to update the field after the model
        instance has been created.

        See https://github.com/FactoryBoy/factory_boy/issues/102 for more.
        """
        created_datetime = kwargs.pop('created_on', None)
        obj = super()._create(
            target_class, *args, **kwargs,
        )
        if created_datetime is not None:
            obj.created_on = created_datetime
            obj.save()
        return obj


class GreatExportEnquiryFactory(factory.django.DjangoModelFactory):
    """
    Ingested Great Export Enquiry data factory
    """

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
    data_enquiry = ''
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
        self.data_markets.set([CountryFactory()])

    class Meta:
        model = 'company_activity.GreatExportEnquiry'


class CompanyActivityGreatExportEnquiryFactory(CompanyActivityBaseFactory):
    """
    CompanyActivity factory with an great export enquiry.
    """

    activity_source = CompanyActivity.ActivitySource.great
    great = factory.SubFactory(GreatExportEnquiryFactory)

    class Meta:
        model = 'company_activity.CompanyActivity'

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """
        Overwrite the _create to prevent the CompanyActivity from saving to the database.
        This is due to the great export enquiry already creating the CompanyActivity inside its
        model save.
        """
        obj = model_class(*args, **kwargs)
        return CompanyActivity.objects.get(great_id=obj.great_id)
