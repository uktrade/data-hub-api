import factory

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory


class CompanyReferralFactory(factory.django.DjangoModelFactory):
    """A factory for outstanding referrals."""

    company = factory.SubFactory(CompanyFactory)
    contact = factory.SubFactory(ContactFactory, company=factory.SelfAttribute('..company'))
    recipient = factory.SubFactory(AdviserFactory)
    subject = factory.Faker('sentence', nb_words=8)
    notes = factory.Faker('paragraph', nb_sentences=10)

    class Meta:
        model = 'company_referral.CompanyReferral'
