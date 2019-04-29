On the 4th of May 2019, all data in the ``company_company`` registered address fields will be replaced by the official data from the Companies House record identified by the ``company_company.company_number`` field.
In cases where ``company_company.company_number`` is invalid or blank (e.g. for non-UK companies), the registered address fields will be made blank and the related data lost.
List of registered address fields:

- ``registered_address_1``
- ``registered_address_2``
- ``registered_address_town``
- ``registered_address_county``
- ``registered_address_postcode``
- ``registered_address_country_id``
