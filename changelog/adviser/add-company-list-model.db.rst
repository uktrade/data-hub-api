A ``company_list_companylist`` table with the following columns was created:

- ``"created_on" timestamp with time zone NULL``
- ``"modified_on" timestamp with time zone NULL``
- ``"id" uuid NOT NULL PRIMARY KEY``
- ``"name" varchar(255) NOT NULL``
- ``"is_legacy_default" boolean NOT NULL``
- ``"adviser_id" uuid NOT NULL``
- ``"created_by_id" uuid NULL``
- ``"modified_by_id" uuid NULL``

This will be used to store the IDs and names of user-created lists of companies.
