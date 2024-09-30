import factory.fuzzy
from django.utils.timezone import now

from datahub.company.test.factories import CompanyFactory
from datahub.company_activity.models import CompanyActivity
from datahub.company_referral.test.factories import CompanyReferralFactory
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.metadata.test.factories import CountryFactory


class CompanyActivityInteractionFactory(factory.django.DjangoModelFactory):
    """
    CompanyActivity factory with an interaction.

    Be careful for tests as creating an Interaction already creates a CompanyActivity
    for the interaction, so calling this creates two CompanyActivities.
    """

    date = now()
    activity_source = CompanyActivity.ActivitySource.interaction
    company = factory.SubFactory(CompanyFactory)
    interaction = factory.SubFactory(CompanyInteractionFactory)
    referral = None
    investment = None

    class Meta:
        model = 'company_activity.CompanyActivity'

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """
        Overwrite the _create to prevent the CompanyActivity from saving to the database.
        This is due to the Interaction already creating the CompanyActivity inside its
        model save.
        """
        obj = model_class(*args, **kwargs)
        return CompanyActivity.objects.get(interaction_id=obj.interaction_id)


class CompanyActivityReferralFactory(factory.django.DjangoModelFactory):
    """
    CompanyActivity factory with a referral.
    """

    date = now()
    activity_source = CompanyActivity.ActivitySource.referral
    company = factory.SubFactory(CompanyFactory)
    referral = factory.SubFactory(CompanyReferralFactory)
    interaction = None
    investment = None

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


class CompanyActivityInvestmentProjectFactory(factory.django.DjangoModelFactory):
    """
    CompanyActivity factory with an investment project.
    """

    date = now()
    activity_source = CompanyActivity.ActivitySource.investment
    company = factory.SubFactory(CompanyFactory)
    investment = factory.SubFactory(InvestmentProjectFactory)
    interaction = None
    referral = None

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


class CompanyActivityIngestedFileFactory(factory.django.DjangoModelFactory):
    """
    CompanyActivity ingested file factory
    """

    filepath = 'data-flow/exports/GreatGovUKFormsPipeline/20240920T000000/full_ingestion.jsonl.gz'
    created_on = now()

    class Meta:
        model = 'company_activity.IngestedFile'


class CompanyActivityGreatFactory(factory.django.DjangoModelFactory):
    """
    CompanyActivity ingested Great data factory
    """

    form_id = 'dit:directoryFormsApi:Submission:9034'
    published = now()
    url = '"http://www.lewis.com/"'

    attributed_to_type = 'dit:directoryFormsApi:SubmissionAction:gov-notify-email'
    attributed_to_id = 'dit:directoryFormsApi:SubmissionType:Unknown'

    meta_action_name = 'gov-notify-email'
    meta_template_id = '07f729e9-8561-4180-a6ff-b14e6be1fef0'
    meta_email_address = 'dcarter@example.com'

    data_comment = 'some comment'
    data_country = factory.SubFactory(CountryFactory)
    data_full_name = 'Charlie Smith'
    data_website_url = 'http://www.smith-hall.com/'
    data_company_name = 'Smith-Jenkins'
    data_company_size = '1-10'
    data_phone_number = '12345678'
    data_terms_agreed = False
    data_email_address = 'christian31@example.com'
    data_opportunities = '[https://www.hoover-ramos.com/explore/wp-content/explorelogin.php]'
    data_role_in_company = 'test'
    data_opportunity_urls = 'http://moore.com/listpost.html'

    actor_type = 'dit:directoryFormsApi:Submission:Sender'
    actor_id = 'dit:directoryFormsApi:Sender:1041'
    actor_dit_email_address = 'crystalbrock@example.org'
    actor_dit_is_blacklisted = False
    actor_dit_is_whitelisted = False
    actor_dit_blacklisted_reason = ''

    class Meta:
        model = 'company_activity.Great'
