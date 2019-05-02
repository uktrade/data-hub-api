import factory

from datahub.company.test.factories import CompanyFactory


class DnBMatchingResultFactory(factory.django.DjangoModelFactory):
    """DnBMatchingResult factory."""

    company = factory.SubFactory(CompanyFactory)
    data = {}

    class Meta:
        model = 'dnb_match.DnBMatchingResult'


class DnBMatchingCSVRecord(factory.django.DjangoModelFactory):
    """DnBMatchingCSVRecord factory."""

    company_id = factory.SelfAttribute('company.id')
    company = factory.SubFactory(CompanyFactory)
    batch_number = 1
    data = {}

    class Meta:
        exclude = ('company',)
        model = 'dnb_match.DnBMatchingCSVRecord'
