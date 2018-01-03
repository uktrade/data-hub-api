import uuid
import factory

from datahub.core.constants import Country

from .. import constants


class InvoiceFactory(factory.django.DjangoModelFactory):
    """Invoice factory."""

    id = factory.LazyFunction(uuid.uuid4)
    invoice_number = factory.Faker('pystr')

    billing_company_name = factory.Faker('text')
    billing_contact_name = factory.Faker('name')
    billing_address_1 = factory.Sequence(lambda n: f'Apt {n}.')
    billing_address_2 = factory.Sequence(lambda n: f'{n} Foo st.')
    billing_address_country_id = Country.united_kingdom.value.id
    billing_address_county = factory.Faker('text')
    billing_address_postcode = factory.Faker('postcode')
    billing_address_town = factory.Faker('city')

    invoice_company_name = constants.DIT_COMPANY_NAME
    invoice_address_1 = constants.DIT_ADDRESS_1
    invoice_address_2 = constants.DIT_ADDRESS_2
    invoice_address_town = constants.DIT_ADDRESS_TOWN
    invoice_address_county = constants.DIT_ADDRESS_COUNTY
    invoice_address_postcode = constants.DIT_ADDRESS_POSTCODE
    invoice_address_country_id = constants.DIT_ADDRESS_COUNTRY_ID
    invoice_vat_number = constants.DIT_VAT_NUMBER
    payment_due_date = factory.Faker('future_date')

    contact_email = factory.Faker('email')

    class Meta:
        model = 'omis-invoice.Invoice'
