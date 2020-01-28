import factory

from datahub.investment.project.evidence.models import EvidenceDocument, EvidenceTag
from datahub.investment.project.test.factories import InvestmentProjectFactory


class EvidenceTagFactory(factory.django.DjangoModelFactory):
    """Evidence tag factory."""

    name = factory.Faker('sentence', nb_words=2)

    class Meta:
        model = EvidenceTag


class EvidenceDocumentFactory(factory.django.DjangoModelFactory):
    """Evidence document factory."""

    original_filename = factory.Faker('file_name')
    investment_project = factory.SubFactory(InvestmentProjectFactory)
    comment = factory.Faker('paragraph', nb_sentences=3)

    class Meta:
        model = EvidenceDocument
