import factory
from django.utils.timezone import now


class CompanyFactory(factory.django.DjangoModelFactory):
    """Company factory."""

    name = factory.Sequence(lambda x: 'name{0}'.format(x))
    archived = False
    
    class Meta:
        model = 'company.Company'


class CompaniesHouseCompanyFactory(factory.django.DjangoModelFactory):
    """Companies house company factory."""

    name = factory.Sequence(lambda x: 'name{0}'.format(x))
    company_number = factory.Sequence(lambda x: x)
    incorporation_date = now()

    class Meta:
        model = 'company.CompaniesHouseCompany'


class ContactFactory(factory.django.DjangoModelFactory):
    """Contact factory"""

    name = factory.Sequence(lambda x: 'name{0}'.format(x))
    company = factory.SubFactory(CompanyFactory)

    class Meta:
        model = 'company.Contact'


class InteractionFactory(factory.django.DjangoModelFactory):
    """Interaction factory."""

    company = factory.SubFactory(CompanyFactory)
    contact = factory.SubFactory(ContactFactory)
    subject = 'foo'

    class Meta:
        model = 'company.Interaction'
