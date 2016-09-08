MAPPINGS = {
    'AccountSet': {
        'to': 'company',
        'local': (
            ('AccountId', 'id'),
            ('optevia_CompaniesHouseNumber', 'company_number'),
            ('optevia_ukorganisation', 'uk_based'),
            ('optevia_BusinessType_Id', 'business_type'),
            (None, 'registered_name'),
            ('Name', 'trading_name'),
            ('optevia_Sector_Id', 'sectors'),
            ('WebSiteURL', 'website'),
            ('optevia_EmployeeRange_Id', 'number_of_employees'),
            ('optevia_TurnoverRange_Id', 'annual_turnover'),
            ('Address1_Line1', 'trading_address_1'),
            ('Address1_Line2', 'trading_address_2'),
            ('Address1_City', 'trading_address_town'),
            ('Address1_County', 'trading_address_county'),
            ('Address1_County', 'trading_address_country'),
            ('Address1_PostalCode', 'trading_address_postcode'),
            ('optevia_UKRegion_Id', 'region'),
            (None, 'account_manager'),
            (None, 'countries_of_interest'),
            (None, 'currently_exporting_to'),
            (None, 'connections'),
        )
    },
    'ContactSet': {
        'to': 'contact',
        'local': (
            ('ContactId', 'id'),
            ('optevia_Title_Id', 'title'),
            ('FirstName', 'first_name'),
            ('LastName', 'last_name'),
            ('optevia_ContactRole_Id', 'role'),
            ('optevia_TelephoneNumber'  'phone'),  # many other options
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
            ('AccountId_Id', 'company'),
        )
    },
    'optevia_activitylinkSet': {
        'to': 'interaction',
        'local': (
            ('optevia_activitylinkId', 'id'),
            ('optevia_InteractionCommunicationChannel_Id', 'interaction_type'),
            ('optevia_Subject', 'subject'),
            ('optevia_Date', 'date_of_interaction'),
            ('optevia_Advisor_Id', 'advisor'),
            ('optevia_Contact_Id', 'contact'),
            ('optevia_Organisation_Id', 'company'),
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
