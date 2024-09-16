import factory.fuzzy
from django.utils.timezone import now

from datahub.company.test.factories import CompanyFactory
from datahub.company_activity.models import CompanyActivity
from datahub.company_referral.test.factories import CompanyReferralFactory
from datahub.interaction.test.factories import CompanyInteractionFactory


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
