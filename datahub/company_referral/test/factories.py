from datetime import timezone

import factory

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.company_referral.models import CompanyReferral
from datahub.interaction.test.factories import CompanyInteractionFactory


class CompanyReferralFactory(factory.django.DjangoModelFactory):
    """A factory for outstanding referrals."""

    company = factory.SubFactory(CompanyFactory)
    contact = factory.SubFactory(ContactFactory, company=factory.SelfAttribute('..company'))
    recipient = factory.SubFactory(AdviserFactory)
    subject = factory.Faker('sentence', nb_words=8)
    notes = factory.Faker('paragraph', nb_sentences=10)
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SelfAttribute('created_by')

    class Meta:
        model = 'company_referral.CompanyReferral'


class ClosedCompanyReferralFactory(CompanyReferralFactory):
    """A factory for referrals that have been closed."""

    status = CompanyReferral.Status.CLOSED


class CompleteCompanyReferralFactory(CompanyReferralFactory):
    """A factory for referrals that have been completed."""

    status = CompanyReferral.Status.COMPLETE
    interaction = factory.SubFactory(CompanyInteractionFactory)
    completed_by = factory.SubFactory(AdviserFactory)
    completed_on = factory.Faker('past_datetime', tzinfo=timezone.utc)
