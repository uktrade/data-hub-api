import factory
from django.utils.timezone import now

from datahub.company.test.factories import AdviserFactory
from datahub.investment.project.report.models import SPIReport


class SPIReportFactory(factory.django.DjangoModelFactory):
    """Investment project report factory."""

    s3_key = factory.Faker('slug')

    created_on = now()
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SelfAttribute('created_by')

    class Meta:
        model = SPIReport
