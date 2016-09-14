from korben import config
from korben import services


MAPPINGS = {
    'AccountSet': {
        'to': 'api_company',
        'local': (
            ('AccountId', 'id'),
            ('optevia_CompaniesHouseNumber', 'company_number'),
            ('optevia_ukorganisation', 'uk_based'),
            ('optevia_BusinessType_Id', 'business_type'),

            # not null wtf
            # (None, 'registered_name'),
            ('Name', 'registered_name'),

            ('Name', 'trading_name'),
            ('optevia_Sector_Id', 'sectors'),
            ('WebSiteURL', 'website'),
            ('optevia_EmployeeRange_Name', 'number_of_employees'),  # should be UUID fffff
            ('optevia_TurnoverRange_Name', 'annual_turnover'),  # should be UUID fffff
            ('Address1_Line1', 'trading_address_1'),
            ('Address1_Line2', 'trading_address_2'),
            ('Address1_City', 'trading_address_town'),
            ('Address1_County', 'trading_address_county'),
            ('Address1_County', 'trading_address_country'),
            ('Address1_PostalCode', 'trading_address_postcode'),
            ('optevia_UKRegion_Name', 'region'),  # should be UUID fffff
            (None, 'account_manager'),
            (None, 'countries_of_interest'),
            (None, 'currently_exporting_to'),
            (None, 'connections'),
        )
    },
    'ContactSet': {
        'to': 'api_contact',
        'local': (
            ('ContactId', 'id'),
            ('optevia_Title_Name', 'title'),  # should be UUID fffff
            ('FirstName', 'first_name'),
            ('LastName', 'last_name'),
            ('optevia_ContactRole_Id', 'role'),
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
        )
    },
    'optevia_activitylinkSet': {
        'to': 'api_interaction',
        'local': (
            ('optevia_activitylinkId', 'id'),
            ('optevia_InteractionCommunicationChannel_Name', 'interaction_type'),  # should be UUID fffff
            ('optevia_Subject', 'subject'),
            ('optevia_Date', 'date_of_interaction'),
            ('optevia_Advisor_Id', 'advisor'),
            ('optevia_Contact_Id', 'contact_id'),
            ('optevia_Organisation_Id', 'company_id'),
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
    }
}

ES_STRING_ANALYZED = {'type': 'string', 'index': 'analyzed'}
ES_STRING_NOT_ANALYZED = {'type': 'string', 'index': 'not_analyzed'}
ES_STRING_NO = {'type': 'string', 'index': 'no'}


def update(original_dict, update_dict):
    updated_dict = dict(original_dict)
    updated_dict.update(update_dict)
    return updated_dict


ES_INDEX = 'datahub'
ES_TYPES = {
    table.name: {
        'properties': {
            col.name: ES_STRING_ANALYZED
            for col in table.colums
        }
    }
    for table in services.db.poll_for_metadata(config.database_url).tables
}
