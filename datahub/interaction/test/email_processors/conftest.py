import factory
import pytest

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory


@pytest.fixture()
def calendar_data_fixture():
    """
    Create advisers, contacts and companies so that our email samples can be
    attributed to some DB entities.
    """
    adviser_emails = [
        'adviser1@trade.gov.uk',
        'adviser2@digital.trade.gov.uk',
    ]
    AdviserFactory.create_batch(
        len(adviser_emails),
        email=factory.Iterator(adviser_emails),
        contact_email=factory.SelfAttribute('email'),
    )
    AdviserFactory(
        email='adviser3@digital.trade.gov.uk',
        contact_email='correspondence3@digital.trade.gov.uk',
    )
    company_1 = CompanyFactory(name='Company 1')
    company_2 = CompanyFactory(name='Company 2')
    contacts = [
        ('Bill Adama', company_1),
        ('Saul Tigh', company_1),
        ('Laura Roslin', company_2),
    ]
    for name, company in contacts:
        first_name, last_name = name.split(' ')
        email_prefix = name.lower().replace(' ', '.')
        email = f'{email_prefix}@example.net'
        ContactFactory(
            first_name=first_name,
            last_name=last_name,
            email=email,
            company=company,
        )
    yield
