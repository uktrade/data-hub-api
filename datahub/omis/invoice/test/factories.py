import uuid
import factory

from .. import constants


class InvoiceFactory(factory.django.DjangoModelFactory):
    """Invoice factory."""

    id = factory.LazyFunction(uuid.uuid4)
    invoice_number = factory.Faker('pystr')
    invoice_company_name = constants.DIT_COMPANY_NAME
    invoice_address_1 = constants.DIT_ADDRESS_1
    invoice_address_2 = constants.DIT_ADDRESS_2
    invoice_address_town = constants.DIT_ADDRESS_TOWN
    invoice_address_county = constants.DIT_ADDRESS_COUNTY
    invoice_address_postcode = constants.DIT_ADDRESS_POSTCODE
    invoice_address_country_id = constants.DIT_ADDRESS_COUNTRY_ID
    invoice_vat_number = constants.DIT_VAT_NUMBER

    class Meta:  # noqa: D101
        model = 'omis-invoice.Invoice'
