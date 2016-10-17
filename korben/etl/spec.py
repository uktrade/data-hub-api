import csv
import os
import collections
from korben import services

MAPPINGS = {}

CONSTANT_MAPPINGS = (
    ('optevia_businesstypeId', 'optevia_businesstypeSet', 'optevia_name', 'company_businesstype'),
    ('optevia_sectorId', 'optevia_sectorSet', 'optevia_name', 'company_sector'),
    ('optevia_employeerangeId', 'optevia_employeerangeSet', 'optevia_name', 'company_employeerange'),
    ('optevia_turnoverrangeId', 'optevia_turnoverrangeSet', 'optevia_name', 'company_turnoverrange'),
    ('optevia_ukregionId', 'optevia_ukregionSet', 'optevia_name', 'company_ukregion'),
    ('optevia_countryId', 'optevia_countrySet', 'optevia_Country', 'company_country'),
    ('optevia_titleId', 'optevia_titleSet', 'optevia_name', 'company_title'),
    ('optevia_contactroleId', 'optevia_contactroleSet', 'optevia_name', 'company_role'),
    ('optevia_interactioncommunicationchannelId', 'optevia_interactioncommunicationchannelSet', 'optevia_name', 'company_interactiontype'),
    ('TeamId', 'TeamSet', 'Name', 'company_team'),
)


for source_pkey, source_table, source_name, target_table in CONSTANT_MAPPINGS:
    MAPPINGS.update({
        source_table: {
            'to': target_table,
            'local': (
                (source_pkey, 'id'),
                (source_name, 'name'),
            ),
        },
    })

MAPPINGS.update({
    'AccountSet': {
        'to': 'company_company',
        'local': (
            ('AccountId', 'id'),
            ('Name', 'name'),
            ('optevia_Alias', 'alias'),
            ('optevia_CompaniesHouseNumber', 'company_number'),
            # ('optevia_ukorganisation', 'uk_based'), requires serialiser
            ('optevia_BusinessType_Id', 'business_type_id'),
            ('optevia_Sector_Id', 'sector_id'),
            # ('optevia_EmployeeRange_Id', 'employee_range_id'), do these stay?
            # ('optevia_TurnoverRange_Id', 'turnover_range_id'),
            ('optevia_Address1', 'registered_address_1'),
            ('optevia_Address2', 'registered_address_2'),
            ('optevia_Address3', 'registered_address_3'),
            ('optevia_Address4', 'registered_address_4'),
            ('optevia_TownCity', 'registered_address_town'),
            ('optevia_StateCounty', 'registered_address_county'),
            ('optevia_PostCode', 'registered_address_postcode'),
            ('optevia_Country_Id', 'registered_address_country_id'),
            # ('optevia_UKRegion_Id', 'uk_region_id'), did it fall out?
            ('Description', 'description'),
            ('ModifiedOn', 'modified_on'),
            ('CreatedOn', 'created_on'),
        ),
        'local_fn': (
            ((), 'archived', lambda: False),
        ),
    },
    'SystemUserSet': {
        'to': 'company_advisor',
        'local': (
            ('SystemUserId', 'id'),
        ),
        'local_fn': (
            (('FirstName', 'LastName'), 'name', lambda first, last: "{0} {1}".format(first, last)),  # NOQA
        ),
    },
    'ContactSet': {
        'to': 'company_contact',
        'local': (
            ('Title', 'title_id'),
            ('FirstName', 'first_name'),
            ('LastName', 'last_name'),
            # ('MiddleName', None),  data migration to move these
            # ('optevia_LastVerified', None)  korben magic to add current on write
            ('ParentCustomerId_Id', 'company_id'),
            ('optevia_PrimaryContact', 'primary'),
            ('optevia_CountryCode', 'telephone_countrycode'),
            # ('optevia_AreaCode` `++` `optevia_TelephoneNumber` | `← * →` | `telephone_number` | Telephone number | Korben to fill area code |
            ('EMailAddress1', 'email'),
            ('optevia_Address1', 'address_1'),
            ('optevia_Address2', 'address_2'),
            ('optevia_Address3', 'address_3'),
            ('optevia_Address4', 'address_4'),
            ('optevia_TownCity', 'address_town'),
            ('optevia_StateCounty', 'address_county'),
            ('optevia_PostCode', 'address_postcode'),
            ('optevia_Country_Id', 'address_country_id'),
            ('optevia_UKRegion_Id', 'uk_region_id'),

            # ('ModifiedOn', 'modified_on'),  not wanted in leeloo?
            # ('CreatedOn', 'created_on'),
        ),
    },

    # check commit history for more information
    'detica_interactionSet': {
        'to': 'company_interaction',
        'local': (
            ('ActivityId', 'id'),
            (
                'optevia_InteractionCommunicationChannel_Id',
                'interaction_type_id',
            ),
            ('Subject', 'subject'),
            ('ActualStart', 'date_of_interaction'),
            ('optevia_Advisor_Id', 'advisor_id'),
            ('optevia_Contact_Id', 'contact_id'),
            ('optevia_Organisation_Id', 'company_id'),
            ('optevia_Notes', 'notes'),

            ('ModifiedOn', 'modified_on'),
            ('CreatedOn', 'created_on'),
        ),
        'local_fn': (
            ((), 'archived', lambda: False),
        ),
    },
})

DJANGO_LOOKUP = {mapping['to']: name for name, mapping in MAPPINGS.items()}


ES_STRING_ANALYZED = {'type': 'string', 'index': 'analyzed'}
ES_STRING_NOT_ANALYZED = {'type': 'string', 'index': 'not_analyzed'}
ES_STRING_NO = {'type': 'string', 'index': 'no'}


def update(original_dict, update_dict):
    'Copy original_dict and update with update_dict'
    updated_dict = dict(original_dict)
    updated_dict.update(update_dict)
    return updated_dict

ES_INDEX = 'datahub'
_ES_TYPES = None


def get_es_types():
    'since this introspects the db to get table information, it must be called'
    global _ES_TYPES
    if _ES_TYPES is not None:
        return _ES_TYPES
    _ES_TYPES = {}
    tables = services.db.get_django_metadata().tables.values()
    for table in tables:  # NOQA
        if table.name not in DJANGO_LOOKUP:
            continue
        properties = {}
        for column in table.columns:
            # TODO: do a little type introspection for bools
            if not column.foreign_keys:
                properties[column.name] = ES_STRING_ANALYZED
            else:
                column_name = column.name[:-3]  # strip `_id` suffix
                properties[column_name] = ES_STRING_ANALYZED
        _ES_TYPES[table.name] = {'properties': properties}
    return _ES_TYPES


COLNAME_LONGSHORT = {}
COLNAME_SHORTLONG = {}
_COLNAME_MAPPING_PATH = os.path.join(
    os.path.dirname(__file__), 'cdms-psql-column-mapping.csv'
)
with open(_COLNAME_MAPPING_PATH) as fh:
    for table_name, long_col, short_col in csv.reader(fh):
        COLNAME_LONGSHORT[(table_name, long_col)] = short_col
        COLNAME_SHORTLONG[(table_name, short_col)] = long_col
