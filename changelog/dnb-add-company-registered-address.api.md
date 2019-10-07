The `POST /v4/dnb/company-create` API endpoint will now save `registered_address_*`
fields on Data Hub companies that it creates. Registered address fields will not be
saved at all unless a minimum of `line_1`, `town` and `country` fields are provided.
