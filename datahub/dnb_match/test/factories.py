import factory

from datahub.company.test.factories import CompanyFactory


class DnBMatchingResultFactory(factory.django.DjangoModelFactory):
    """DnBMatchingResult factory."""

    company = factory.SubFactory(CompanyFactory)
    data = {}

    class Meta:
        model = 'dnb_match.DnBMatchingResult'
