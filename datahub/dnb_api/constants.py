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
    # TODO: Uncomment when D&B fix their data and add to CompanySerializer.dnb_read_only_fields
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
    # TODO: Uncomment when D&B fix their data and add to CompanySerializer.dnb_read_only_fields
    # 'website',
    'global_ultimate_duns_number',
    'company_number',
)
