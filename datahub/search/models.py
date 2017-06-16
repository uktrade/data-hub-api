from django.conf import settings
from elasticsearch_dsl import Boolean, Date, DocType, Double, Integer, Nested, String


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


def _id_uri_dict(obj):
    """Creates dictionary with selected field from supplied object."""
    return {
        'id': str(obj.id),
        'uri': obj.uri
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

    IGNORED_FIELDS = ()

    MAPPINGS = {}

    @classmethod
    def es_document(cls, dbmodel):
        """Creates Elasticsearch document."""
        source = cls.dbmodel_to_dict(dbmodel)

        return {
            '_index': settings.ES_INDEX,
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

    IGNORED_FIELDS = (
        'children', 'servicedeliverys', 'investor_investment_projects',
        'intermediate_investment_projects', 'investee_projects',
        'tree_id', 'lft', 'rght', 'business_leads', 'interactions',
    )

    class Meta:
        """Default document meta data."""

        index = settings.ES_INDEX
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
    adviser = Nested(properties={'id': String(index='not_analyzed'),
                                 'first_name': String(copy_to='adviser.name'),
                                 'last_name': String(copy_to='adviser.name'),
                                 'name': String(),
                                 })  # Adviser
    archived_by = Nested(properties={'id': String(index='not_analyzed'),
                                     'first_name': String(copy_to='archived_by.name'),
                                     'last_name': String(copy_to='archived_by.name'),
                                     'name': String(),
                                     })
    company = Nested(properties={'id': String(index='not_analyzed'), 'name': String()})

    MAPPINGS = {
        'id': str,
        'title': _id_name_dict,
        'address_country': _id_name_dict,
        'adviser': _contact_dict,
        'company': _id_name_dict,
        'archived_by': _contact_dict,
    }

    IGNORED_FIELDS = (
        'interactions', 'servicedeliverys', 'investment_projects',
    )

    class Meta:
        """Default document meta data."""

        index = settings.ES_INDEX
        doc_type = 'contact'


class InvestmentProject(DocType, MapDBModelToDict):
    """Elasticsearch representation of InvestmentProject."""

    id = String(index='not_analyzed')
    approved_commitment_to_invest = Boolean()
    approved_fdi = Boolean()
    approved_good_value = Boolean()
    approved_high_value = Boolean()
    approved_landed = Boolean()
    approved_non_fdi = Boolean()
    actual_land_date = Date()
    actual_land_date_documents = Nested(properties={
        'id': String(index='not_analyzed'),
        'uri': String(index='not_analyzed')
    })  # Documents
    business_activities = Nested(properties={
        'id': String(index='not_analyzed'),
        'name': String()
    })  # BusinessActivities
    client_contacts = Nested(properties={'id': String(index='not_analyzed'),
                                         'first_name': String(copy_to='client_contacts.name'),
                                         'last_name': String(copy_to='client_contacts.name'),
                                         'name': String(),
                                         })  # ContactArray
    client_relationship_manager = Nested(properties={
        'id': String(index='not_analyzed'),
        'name': String()}
    )  # Adviser
    project_manager = Nested(properties={
        'id': String(index='not_analyzed'),
        'name': String()}
    )  # Adviser
    archived = Boolean()
    archived_reason = String()
    archived_by = Nested(properties={'id': String(index='not_analyzed'),
                                     'first_name': String(copy_to='archived_by.name'),
                                     'last_name': String(copy_to='archived_by.name'),
                                     'name': String(),
                                     })
    created_on = Date()
    modified_on = Date()
    description = String()
    estimated_land_date = Date()
    fdi_type = Nested(properties={
        'id': String(index='not_analyzed'),
        'name': String()
    })  # FDIType
    fdi_type_documents = Nested(properties={
        'id': String(index='not_analyzed'),
        'uri': String(index='not_analyzed')
    })  # Documents
    intermediate_company = Nested(properties={
        'id': String(index='not_analyzed'),
        'name': String()
    })  # CompanySlim
    uk_company = Nested(properties={
        'id': String(index='not_analyzed'),
        'name': String()
    })  # CompanySlim
    investor_company = Nested(properties={
        'id': String(index='not_analyzed'),
        'name': String()
    })  # CompanySlim
    investment_type = Nested(properties={
        'id': String(index='not_analyzed'),
        'name': String()
    })  # InvestmentType
    name = String()
    description = String()
    r_and_d_budget = Boolean()
    non_fdi_r_and_d_budget = Boolean()
    new_tech_to_uk = Boolean()
    export_revenue = Boolean()
    site_decided = Boolean()
    nda_signed = Boolean()
    government_assistance = Boolean()
    client_cannot_provide_total_investment = Boolean()
    total_investment = Double()
    foreign_equity_investment = Double()
    number_new_jobs = Integer()
    non_fdi_type = Nested(properties={
        'id': String(index='not_analyzed'),
        'name': String()
    })  # NonFDIType
    not_shareable_reason = String()
    operations_commenced_documents = Nested(properties={
        'id': String(index='not_analyzed'),
        'uri': String(index='not_analyzed')
    })  # Documents
    phase = Nested(properties={
        'id': String(index='not_analyzed'),
        'name': String()
    })  # Phase
    project_code = String(index='not_analyzed')
    project_shareable = Boolean()
    referral_source_activity = Nested(properties={
        'id': String(index='not_analyzed'),
        'name': String()
    })  # ReferralSourceActivity
    referral_source_activity_marketing = Nested(properties={
        'id': String(index='not_analyzed'),
        'name': String()
    })  # ReferralSourceActivityMarketing
    referral_source_activity_website = Nested(properties={
        'id': String(index='not_analyzed'),
        'name': String()
    })  # ReferralSourceActivityWebsite
    referral_source_activity_event = String()
    referral_source_advisor = Nested(properties={'id': String(index='not_analyzed'),
                                                 'first_name': String(copy_to='referral_source_advisor.name'),
                                                 'last_name': String(copy_to='referral_source_advisor.name'),
                                                 'name': String(),
                                                 })  # Adviser
    sector = Nested(properties={
        'id': String(index='not_analyzed'),
        'name': String()
    })  # Sector
    average_salary = Nested(properties={
        'id': String(index='not_analyzed'),
        'name': String()
    })  # AverageSalary

    MAPPINGS = {
        'id': str,
        'actual_land_date_documents': lambda col: [_id_uri_dict(c) for c in col.all()],
        'business_activities': lambda col: [_id_name_dict(c) for c in col.all()],
        'client_contacts': lambda col: [_contact_dict(c) for c in col.all()],
        'client_relationship_manager': _id_name_dict,
        'fdi_type': _id_name_dict,
        'fdi_type_documents': lambda col: [_id_uri_dict(c) for c in col.all()],
        'intermediate_company': _id_name_dict,
        'investor_company': _id_name_dict,
        'uk_company': _id_name_dict,
        'investment_type': _id_name_dict,
        'non_fdi_type': _id_name_dict,
        'operations_commenced_documents': lambda col: [_id_uri_dict(c) for c in col.all()],
        'phase': _id_name_dict,
        'referral_source_activity': _id_name_dict,
        'referral_source_activity_marketing': _id_name_dict,
        'referral_source_activity_website': _id_name_dict,
        'referral_source_adviser': _contact_dict,
        'sector': _id_name_dict,
        'project_code': str,
        'average_salary': _id_name_dict,
        'archived_by': _contact_dict,
    }

    IGNORED_FIELDS = (
        'investmentprojectcode', 'competitor_countries',
        'uk_region_locations', 'strategic_drivers',
        'client_considering_other_countries', 'cdms_project_code',
        'interactions',
    )

    class Meta:
        """Default document meta data."""

        index = settings.ES_INDEX
        doc_type = 'investment_project'
