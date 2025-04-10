import factory
import pytest

from datahub.company.models import Contact
from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.interaction.test.factories import CompanyInteractionFactory


@pytest.fixture
def interaction_email_fixture():
    """Create advisers, contacts and companies so that our email samples can be
    attributed to some DB entities.
    """
    advisers = [
        ('adviser1@trade.gov.uk', 'Adviser', '1'),
        ('adviser2@digital.trade.gov.uk', 'Adviser', '2'),
    ]
    AdviserFactory.create_batch(
        len(advisers),
        email=factory.Iterator(advisers, getter=lambda a: a[0]),
        first_name=factory.Iterator(advisers, getter=lambda a: a[1]),
        last_name=factory.Iterator(advisers, getter=lambda a: a[2]),
        contact_email=factory.SelfAttribute('email'),
    )
    AdviserFactory(
        email='adviser3@digital.trade.gov.uk',
        first_name='Adviser',
        last_name='3',
        contact_email='correspondence3@digital.trade.gov.uk',
    )
    company_1 = CompanyFactory(name='Company 1')
    company_2 = CompanyFactory(name='Company 2')
    contacts = [
        ('Bill Adama', company_1),
        ('Saul Tigh', company_1),
        ('Laura Roslin', company_2),
        ('Sharon Valerii', company_1),
        ('Sharon Valerii', company_2),
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
    # Ensure that our contact who appears on multiple companies
    # with a single email address has more interactions for the
    # contact attributed to 'Company 1'
    contact_with_interactions = Contact.objects.get(
        email='sharon.valerii@example.net',
        company=company_1,
    )
    CompanyInteractionFactory(contacts=[contact_with_interactions], company=company_1)
