from django.conf import settings
from elasticsearch_dsl import Boolean, Date, DocType, Nested, String


class Company(DocType):
    """Elasticsearch representation of Company model."""

    account_manager = Nested(properties={'id': String(index='not_analyzed'),
                                         'first_name': String(copy_to='account_manager.name'),
                                         'last_name': String(copy_to='account_manager.name'),
                                         'name': String(),
                                         })
    alias = String()
    archived = Boolean()
    archived_by = Nested(properties={'id': String(index='not_analyzed'),
                                     'first_name': String(copy_to='archived_by.name'),
                                     'last_name': String(copy_to='archived_by.name'),
                                     'name': String(),
                                     })
    contacts = Nested(properties={'id': String(index='not_analyzed'),
                                  'first_name': String(copy_to='contacts.name'),
                                  'last_name': String(copy_to='contacts.name'),
                                  'name': String(),
                                  })
    archived_on = Date()
    archived_reason = String()
    business_type = Nested(properties={'id': String(index='not_analyzed'), 'name': String()})
    classification = Nested(properties={'id': String(index='not_analyzed'), 'name': String()})
    company_number = String()
    companies_house_data = Nested(properties={'id': String(index='not_analyzed'), 'company_number': String()})
    created_on = Date()
    description = String()
    employee_range = Nested(properties={'id': String(index='not_analyzed'), 'name': String()})
    headquarter_type = Nested(properties={'id': String(index='not_analyzed'), 'name': String()})
    id = String(index='not_analyzed')
    modified_on = Date()
    name = String()
    one_list_account_owner = Nested(properties={'id': String(index='not_analyzed'),
                                                'first_name': String(copy_to='one_list_account_owner.name'),
                                                'last_name': String(copy_to='one_list_account_owner.name'),
                                                'name': String(),
                                                })
    parent = Nested(properties={'id': String(index='not_analyzed'), 'name': String()})
    registered_address_1 = String()
    registered_address_2 = String()
    registered_address_3 = String()
    registered_address_4 = String()
    registered_address_country = Nested(properties={'id': String(index='not_analyzed'), 'name': String()})
    registered_address_county = String()
    registered_address_postcode = String()
    registered_address_town = String()
    sector = Nested(properties={'id': String(index='not_analyzed'), 'name': String()})
    trading_address_1 = String()
    trading_address_2 = String()
    trading_address_3 = String()
    trading_address_4 = String()
    trading_address_country = Nested(properties={'id': String(index='not_analyzed'), 'name': String()})
    trading_address_county = String()
    trading_address_postcode = String()
    trading_address_town = String()
    turnover_range = Nested(properties={'id': String(index='not_analyzed'), 'name': String()})
    uk_region = Nested(properties={'id': String(index='not_analyzed'), 'name': String()})
    uk_based = Boolean()
    website = String()
    export_to_countries = Nested(properties={'id': String(index='not_analyzed'), 'name': String()})
    future_interest_countries = Nested(properties={'id': String(index='not_analyzed'), 'name': String()})

    class Meta:
        """Default document meta data."""

        index = settings.ES_INDEX
        doc_type = 'company'


class Contact(DocType):
    """Elasticsearch representation of Contact model."""

    archived = Boolean()
    archived_on = Date()
    archived_reason = String()
    created_on = Date()
    modified_on = Date()
    id = String(index='not_analyzed')
    name = String()
    title = Nested(properties={'id': String(index='not_analyzed'), 'name': String(copy_to='name')})
    first_name = String(copy_to='name')
    last_name = String(copy_to='name')
    primary = Boolean()
    telephone_countrycode = String()
    telephone_number = String()
    email = String()
    address_same_as_company = Boolean()
    address_1 = String()
    address_2 = String()
    address_3 = String()
    address_4 = String()
    address_town = String()
    address_county = String()
    address_postcode = String()
    telephone_alternative = String()
    email_alternative = String()
    notes = String()
    job_title = String()
    contactable_by_dit = Boolean()
    contactable_by_dit_partners = Boolean()
    contactable_by_email = Boolean()
    contactable_by_phone = Boolean()
    address_country = Nested(properties={'id': String(index='not_analyzed'), 'name': String()})
    advisor = Nested(properties={'id': String(index='not_analyzed'), 'name': String()})
    archived_by = Nested(properties={'id': String(index='not_analyzed'), 'name': String()})
    company = Nested(properties={'id': String(index='not_analyzed'), 'name': String()})

    class Meta:
        """Default document meta data."""

        index = settings.ES_INDEX
        doc_type = 'contact'
