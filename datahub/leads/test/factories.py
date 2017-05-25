"""Model instance factories for business leads."""

import uuid

import factory

from datahub.company.test.factories import (
    AdvisorFactory, CompanyFactory
)


class BusinessLeadFactory(factory.django.DjangoModelFactory):
    """Business lead factory."""

    id = factory.Sequence(lambda x: '{0}'.format(uuid.uuid4()))
    first_name = factory.Sequence(lambda x: 'name {0}'.format(x))
    last_name = factory.Sequence(lambda x: 'surname {0}'.format(x))
    company_name = factory.Sequence(lambda x: 'company name {0}'.format(x))
    company = factory.SubFactory(CompanyFactory)
    email = 'foo@bar.com'
    telephone_number = '+44 123456789'
    contactable_by_email = True
    advisor = factory.SubFactory(AdvisorFactory)

    class Meta:
        model = 'leads.BusinessLead'
