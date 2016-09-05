company = (
    ('company', 'AccountSet'),
    (
        'id', 'AccountId',
        'company_number', 'optevia_CompaniesHouseNumber'
        'uk_based', 'optevia_ukorganisation',
        'business_type', 'optevia_BusinessType_Id',
        'registered_name', None,
        'trading_name', 'Name',
        'sectors', 'optevia_Sector_Id',
        'website', 'WebSiteURL',
        'number_of_employees', 'optevia_EmployeeRange_Id',
        'annual_turnover', 'optevia_TurnoverRange_Id',
        'trading_address_1', 'Address1_Line1',
        'trading_address_2', 'Address1_Line2',
        'trading_address_town', 'Address1_City',
        'trading_address_county', 'Address1_County',
        'trading_address_country', 'Address1_County',
        'trading_address_postcode', 'Address1_PostalCode',
        'region', 'optevia_UKRegion_Id',
        'account_manager', None,
        'countries_of_interest', None,
        'currently_exporting_to', None,
        'connections', None,
    )
)

contact = (
    ('contact', None),
    (
        'id',
        'title',
        'first_name',
        'last_name',
        'role',
        'phone',
        'email',
        'address_1',
        'address_2',
        'address_town',
        'address_county',
        'address_country',
        'address_postcode',
        'alt_phone',
        'alt_email',
        'notes',
        'company',
    )
)

interaction = {
}
