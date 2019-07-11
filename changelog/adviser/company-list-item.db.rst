A ``company_list_companylistitem`` table was created with the following columns:

- ``"id" bigserial NOT NULL PRIMARY KEY``
- ``"adviser_id" uuid NOT NULL``
- ``"company_id" uuid NOT NULL``
- ``"created_on" timestamp with time zone NULL``
- ``"modified_on" timestamp with time zone NULL``
- ``"created_by_id" uuid NULL``
- ``"modified_by_id" uuid NULL``

This table will store a list of companies advisers have added to their personal list of companies.
