from elasticsearch_dsl import Boolean, Date, DocType, Nested, String

from datahub.search import elasticsearch


def _id_name_dict(obj):
    """Creates dictionary with selected field from supplied object."""
    return {
        'id': str(obj.id),
        'name': obj.name,
    }


def _id_type_dict(obj):
    """Creates dictionary with selected field from supplied object."""
    return {
        'id': str(obj.id),
        'type': obj.type
    }


def _contact_dict(obj):
    """Creates dictionary with selected field from supplied object."""
    return {
        'id': str(obj.id),
        'first_name': obj.first_name,
        'last_name': obj.last_name,
    }


def _company_dict(obj):
    return {
        'id': str(obj.id),
        'company_number': obj.company_number,
    }


class MapDBModelToDict(object):
    """Helps convert Django models to dictionaries."""

    # there is no typo in 'servicedeliverys' :(
    IGNORED_FIELDS = (
        'subsidiaries', 'servicedeliverys', 'investment_projects',
        'investor_investment_projects', 'intermediate_investment_projects',
        'investee_projects', 'recipient_investment_projects', 'teams',
        'tree_id', 'lft', 'rght', 'business_leads', 'interactions',
    )

    MAPPINGS = {}

    @classmethod
    def es_document(cls, dbmodel):
        """Creates Elasticsearch document."""
        source = cls.dbmodel_to_dict(dbmodel)

        return {
            '_index': elasticsearch.ES_INDEX,
            '_type': cls._doc_type.name,
            '_id': source.get('id'),
            '_source': source,
        }

    @classmethod
    def dbmodel_to_dict(cls, dbmodel):
        """Converts dbmodel instance to a dictionary suitable for ElasticSearch."""
        result = {col: fn(getattr(dbmodel, col)) for col, fn in cls.MAPPINGS.items()
                  if getattr(dbmodel, col, None) is not None}

        fields = [field for field in dbmodel._meta.get_fields() if field.name not in cls.IGNORED_FIELDS]

        obj = {f.name: getattr(dbmodel, f.name) for f in fields if f.name not in result}

        result.update(obj.items())

        return result

    @classmethod
    def dbmodels_to_es_documents(cls, dbmodels):
        """Converts db models to Elasticsearch documents."""
        for dbmodel in dbmodels:
            yield cls.es_document(dbmodel)


class Company(DocType, MapDBModelToDict):
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
    registered_address_country = Nested(properties={'id': String(index='not_analyzed'), 'name': String()})
    registered_address_county = String()
    registered_address_postcode = String()
    registered_address_town = String()
    sector = Nested(properties={'id': String(index='not_analyzed'), 'name': String()})
    trading_address_1 = String()
    trading_address_2 = String()
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

    MAPPINGS = {
        'companies_house_data': _company_dict,
        'account_manager': _contact_dict,
        'archived_by': _contact_dict,
        'one_list_account_owner': _contact_dict,
        'business_type': _id_name_dict,
        'classification': _id_name_dict,
        'employee_range': _id_name_dict,
        'headquarter_type': _id_name_dict,
        'parent': _id_name_dict,
        'registered_address_country': _id_name_dict,
        'sector': _id_name_dict,
        'trading_address_country': _id_name_dict,
        'turnover_range': _id_name_dict,
        'uk_region': _id_name_dict,
        'address_country': _id_name_dict,
        'contacts': lambda col: [_contact_dict(c) for c in col.all()],
        'id': str,
        'uk_based': bool,
        'export_to_countries': lambda col: [_id_name_dict(c) for c in col.all()],
        'future_interest_countries': lambda col: [_id_name_dict(c) for c in col.all()],
    }

    class Meta:
        """Default document meta data."""

        index = elasticsearch.ES_INDEX
        doc_type = 'company'


class Contact(DocType, MapDBModelToDict):
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
    adviser = Nested(properties={'id': String(index='not_analyzed'), 'name': String()})
    archived_by = Nested(properties={'id': String(index='not_analyzed'), 'name': String()})
    company = Nested(properties={'id': String(index='not_analyzed'), 'name': String()})

    MAPPINGS = {
        'id': str,
        'title': _id_name_dict,
        'address_country': _id_name_dict,
        'adviser': _id_name_dict,
        'company': _id_name_dict,
        'archived_by': _contact_dict,
    }

    class Meta:
        """Default document meta data."""

        index = elasticsearch.ES_INDEX
        doc_type = 'contact'
