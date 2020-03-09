FEATURE_FLAG_DNB_COMPANY_UPDATES = 'dnb-company-updates'

ALL_DNB_UPDATED_SERIALIZER_FIELDS = (
    'name',
    'trading_names',
    'address',
    # TODO: Uncomment when D&B fix their data
    # 'registered_address',
    'number_of_employees',
    'is_number_of_employees_estimated',
    'turnover',
    'is_turnover_estimated',
    # TODO: Uncomment when D&B fix their data
    # 'website',
    'global_ultimate_duns_number',
    'company_number',
)

ALL_DNB_UPDATED_MODEL_FIELDS = (
    'name',
    'trading_names',
    'address_1',
    'address_2',
    'address_town',
    'address_county',
    'address_country',
    'address_postcode',
    # TODO: Uncomment when D&B fix their data
    # 'registered_address_1',
    # 'registered_address_2',
    # 'registered_address_town',
    # 'registered_address_county',
    # 'registered_address_country',
    # 'registered_address_postcode',
    'number_of_employees',
    'is_number_of_employees_estimated',
    'turnover',
    'is_turnover_estimated',
    # TODO: Uncomment when D&B fix their data
    # 'website',
    'global_ultimate_duns_number',
    'company_number',
)

CHANGE_REQUEST_FIELD_MAPPING = [
    # (data-hub-api fields, dnb-service fields)
    ('name', 'primary_name'),
    ('trading_names', 'trading_names'),
    ('number_of_employees', 'employee_number'),
    ('turnover', 'annual_sales'),
    ('turnover_currency', 'annual_sales_currency'),
    ('address_line_1', 'address_line_1'),
    ('address_line_2', 'address_line_2'),
    ('address_town', 'address_town'),
    ('address_county', 'address_county'),
    ('address_country', 'address_country'),
    ('address_postcode', 'address_postcode'),
    ('website', 'domain'),
]
