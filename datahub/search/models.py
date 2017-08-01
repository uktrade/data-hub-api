from django.conf import settings
from elasticsearch_dsl import (Boolean, Date, DocType, Double,
                               Integer, Nested, String)


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


def _contact_mapping(field):
    """Mapping for Adviser/Contact fields."""
    return Nested(properties={'id': String(index='not_analyzed'),
                              'first_name': String(copy_to=f'{field}.name'),
                              'last_name': String(copy_to=f'{field}.name'),
                              'name': String(index='not_analyzed'),
                              })


def _id_name_mapping():
    """Mapping for id name fields."""
    return Nested(properties={
        'id': String(index='not_analyzed'),
        'name': String(index='not_analyzed')
    })


def _id_uri_mapping():
    """Mapping for id uri fields."""
    return Nested(properties={
        'id': String(index='not_analyzed'),
        'uri': String(index='not_analyzed')
    })


def _company_mapping():
    """Mapping for id company_number fields."""
    return Nested(properties={
        'id': String(index='not_analyzed'),
        'company_number': String()
    })


class MapDBModelToDict:
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

        fields = [field for field in dbmodel._meta.get_fields()
                  if field.name not in cls.IGNORED_FIELDS]

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

    account_manager = _contact_mapping('account_manager')
    alias = String()
    archived = Boolean()
    archived_by = _contact_mapping('archived_by')
    contacts = _contact_mapping('contacts')
    archived_on = Date()
    archived_reason = String()
    business_type = _id_name_mapping()
    classification = _id_name_mapping()
    company_number = String(index='not_analyzed')
    companies_house_data = _company_mapping()
    created_on = Date()
    description = String()
    employee_range = _id_name_mapping()
    headquarter_type = _id_name_mapping()
    id = String(index='not_analyzed')
    modified_on = Date()
    name = String(copy_to='name_keyword')
    name_keyword = String(analyzer='lowercase_keyword_analyzer')
    one_list_account_owner = _contact_mapping('one_list_account_owner')
    parent = _id_name_mapping()
    registered_address_1 = String()
    registered_address_2 = String()
    registered_address_country = _id_name_mapping()
    registered_address_county = String()
    registered_address_postcode = String()
    registered_address_town = String(index='not_analyzed')
    sector = _id_name_mapping()
    trading_address_1 = String()
    trading_address_2 = String()
    trading_address_country = _id_name_mapping()
    trading_address_county = String()
    trading_address_postcode = String()
    trading_address_town = String(index='not_analyzed')
    turnover_range = _id_name_mapping()
    uk_region = _id_name_mapping()
    uk_based = Boolean()
    website = String()
    export_to_countries = _id_name_mapping()
    future_interest_countries = _id_name_mapping()

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
        'orders', 'created_by', 'modified_by'
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
    name = String(copy_to='name_keyword')
    name_keyword = String(analyzer='lowercase_keyword_analyzer')
    title = _id_name_mapping()
    first_name = String(copy_to='name')
    last_name = String(copy_to='name')
    primary = Boolean()
    telephone_countrycode = String(index='not_analyzed')
    telephone_number = String(index='not_analyzed')
    email = String(index='not_analyzed')
    address_same_as_company = Boolean()
    address_1 = String()
    address_2 = String()
    address_town = String(index='not_analyzed')
    address_county = String(index='not_analyzed')
    address_postcode = String()
    telephone_alternative = String()
    email_alternative = String()
    notes = String()
    job_title = String(index='not_analyzed')
    contactable_by_dit = Boolean()
    contactable_by_dit_partners = Boolean()
    contactable_by_email = Boolean()
    contactable_by_phone = Boolean()
    address_country = _id_name_mapping()
    adviser = _contact_mapping('adviser')
    archived_by = _contact_mapping('archived_by')
    company = _id_name_mapping()

    MAPPINGS = {
        'id': str,
        'title': _id_name_dict,
        'address_country': _id_name_dict,
        'adviser': _contact_dict,
        'company': _id_name_dict,
        'archived_by': _contact_dict,
    }

    IGNORED_FIELDS = (
        'interactions', 'servicedeliverys', 'investment_projects', 'orders',
        'created_by', 'modified_by'
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
    actual_land_date_documents = _id_uri_mapping()
    business_activities = _id_name_mapping()
    client_contacts = _contact_mapping('client_contacts')
    client_relationship_manager = _id_name_mapping()
    project_manager = _contact_mapping('project_manager')
    project_assurance_adviser = _contact_mapping('project_assurance_adviser')
    team_members = _contact_mapping('team_members')
    archived = Boolean()
    archived_reason = String()
    archived_by = _contact_mapping('archived_by')
    created_on = Date()
    modified_on = Date()
    description = String()
    estimated_land_date = Date()
    fdi_type = _id_name_mapping()
    fdi_type_documents = _id_uri_mapping()
    fdi_value = _id_name_mapping()
    intermediate_company = _id_name_mapping()
    uk_company = _id_name_mapping()
    investor_company = _id_name_mapping()
    investment_type = _id_name_mapping()
    name = String(copy_to='name_keyword')
    name_keyword = String(analyzer='lowercase_keyword_analyzer')
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
    non_fdi_type = _id_name_mapping()
    not_shareable_reason = String()
    operations_commenced_documents = _id_uri_mapping()
    stage = _id_name_mapping()
    project_code = String(index='not_analyzed')
    project_shareable = Boolean()
    referral_source_activity = _id_name_mapping()
    referral_source_activity_marketing = _id_name_mapping()
    referral_source_activity_website = _id_name_mapping()
    referral_source_activity_event = String(index='not_analyzed')
    referral_source_advisor = _contact_mapping('referral_source_advisor')
    sector = _id_name_mapping()
    average_salary = _id_name_mapping()

    MAPPINGS = {
        'id': str,
        'actual_land_date_documents': lambda col: [_id_uri_dict(c) for c in col.all()],
        'business_activities': lambda col: [_id_name_dict(c) for c in col.all()],
        'client_contacts': lambda col: [_contact_dict(c) for c in col.all()],
        'client_relationship_manager': _id_name_dict,
        'team_members': lambda col: [_contact_dict(c.adviser) for c in col.all()],
        'fdi_type': _id_name_dict,
        'fdi_type_documents': lambda col: [_id_uri_dict(c) for c in col.all()],
        'intermediate_company': _id_name_dict,
        'investor_company': _id_name_dict,
        'uk_company': _id_name_dict,
        'investment_type': _id_name_dict,
        'non_fdi_type': _id_name_dict,
        'operations_commenced_documents': lambda col: [_id_uri_dict(c) for c in col.all()],
        'stage': _id_name_dict,
        'referral_source_activity': _id_name_dict,
        'referral_source_activity_marketing': _id_name_dict,
        'referral_source_activity_website': _id_name_dict,
        'referral_source_adviser': _contact_dict,
        'sector': _id_name_dict,
        'project_code': str,
        'average_salary': _id_name_dict,
        'archived_by': _contact_dict,
        'project_manager': _contact_dict,
        'project_assurance_adviser': _contact_dict,
    }

    IGNORED_FIELDS = (
        'investmentprojectcode', 'competitor_countries',
        'uk_region_locations', 'strategic_drivers',
        'client_considering_other_countries', 'cdms_project_code',
        'interactions', 'documents', 'created_by', 'modified_by'
    )

    class Meta:
        """Default document meta data."""

        index = settings.ES_INDEX
        doc_type = 'investment_project'
