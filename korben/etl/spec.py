from korben import config
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
            ('optevia_CompaniesHouseNumber', 'company_number'),
            ('optevia_ukorganisation', 'uk_based'),
            ('optevia_BusinessType_Id', 'business_type_id'),
            ('Name', 'name'),
            ('optevia_Sector_Id', 'sector_id'),
            ('WebSiteURL', 'website'),
            ('optevia_EmployeeRange_Id', 'employee_range_id'),
            ('optevia_TurnoverRange_Id', 'turnover_range_id'),
            ('Address1_Line1', 'address_1'),
            ('Address1_Line2', 'address_2'),
            ('Address1_City', 'address_town'),
            ('Address1_County', 'address_county'),
            ('Address1_County', 'address_country'),
            ('Address1_PostalCode', 'address_postcode'),
            ('optevia_Country_Id', 'country_id'),
            ('optevia_UKRegion_Id', 'uk_region_id'),
            ('Description', 'description'),
            ('ModifiedOn', 'modified_on'),
            ('CreatedOn', 'created_on'),
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
            ('ContactId', 'id'),
            ('optevia_Title_Id', 'title_id'),
            ('FirstName', 'first_name'),
            ('LastName', 'last_name'),
            ('optevia_ContactRole_Id', 'role_id'),
            ('optevia_TelephoneNumber', 'phone'),  # many other options
            ('EMailAddress1', 'email'),

            # a great number of address fields, using the first
            ('Address1_Line1', 'address_1'),
            ('Address1_Line2', 'address_2'),
            ('Address1_City', 'address_town'),
            ('Address1_County', 'address_county'),
            ('Address1_Country', 'address_country'),
            ('Address1_PostalCode', 'address_postcode'),

            # many other telephone numbers
            ('Address1_Telephone1', 'alt_phone'),

            # or 'EMailAddress3',
            ('EMailAddress2', 'alt_email'),

            (None, 'notes'),
            ('AccountId_Id', 'company_id'),

            ('ModifiedOn', 'modified_on'),
            ('CreatedOn', 'created_on'),
        ),
    },
    'optevia_activitylinkSet': {
        'to': 'company_interaction',
        'local': (
            ('optevia_activitylinkId', 'id'),
            ('optevia_InteractionCommunicationChannel_Id', 'interaction_type_id'),
            ('optevia_Subject', 'subject'),
            ('optevia_Date', 'date_of_interaction'),
            ('optevia_Advisor_Id', 'advisor_id'),
            ('optevia_Contact_Id', 'contact_id'),
            ('optevia_Organisation_Id', 'company_id'),

            ('ModifiedOn', 'modified_on'),
            ('CreatedOn', 'created_on'),
        ),
        'foreign': (
            (
                (
                    'optevia_Interaction_Id',
                    'optevia_interactionSet',
                    'optevia_Notes'
                ),
                'notes'
            ),
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
ES_TYPES = {}
for table in services.db.poll_for_metadata(config.database_url).tables.values():  # NOQA
    if table.name not in DJANGO_LOOKUP:
        continue
    properties = {}
    for column in table.columns:
        if not column.foreign_keys:
            properties[column.name] = ES_STRING_ANALYZED
        else:
            column_name = column.name[:-3]  # strip `_id` suffix
            properties[column_name] = ES_STRING_ANALYZED
    ES_TYPES[table.name] = {'properties': properties}
