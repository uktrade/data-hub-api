"""Model instance factories for business leads."""

import uuid

import factory

from datahub.company.test.factories import (
    AdviserFactory, CompanyFactory
)


class BusinessLeadFactory(factory.django.DjangoModelFactory):
    """Business lead factory."""

    id = factory.Sequence(lambda _: str(uuid.uuid4()))
    first_name = factory.Sequence(lambda n: 'name {n}')
    last_name = factory.Sequence(lambda n: 'surname {n}')
    company_name = factory.Sequence(lambda n: 'company name {n}')
    company = factory.SubFactory(CompanyFactory)
    email = 'foo@bar.com'
    telephone_number = '+44 123456789'
    contactable_by_email = True
    adviser = factory.SubFactory(AdviserFactory)

    class Meta:  # noqa: D101
        model = 'leads.BusinessLead'
