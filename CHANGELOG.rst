Data Hub API 7.10.0 (2018-11-26)
================================



Deprecations and removals
-------------------------

- **Companies** *(Correction)* The API field ``one_list_account_owner`` is deprecated and will be removed on or after November, 29. The recommended and most efficient way to upgrade is to use the field ``one_list_group_global_account_manager`` instead.

Bug fixes
---------

- The ``delete_old_records`` and ``delete_orphans`` management commands were optimised to use less memory and be faster when run without the ``--simulate`` or ``--only-print-queries`` arguments.

Internal changes
----------------

- Various dependencies were updated.

API
---

- **Companies** *(Correction)* The API field ``one_list_account_owner`` is deprecated and will be removed on or after November, 29. The recommended and most efficient way to upgrade is to use the field ``one_list_group_global_account_manager`` instead.
- **Companies** ``GET /company/<uuid:pk>`` and the other company endpoints now return the read-only field ``one_list_group_global_account_manager`` with details of the One List Global Account Manager for the group that the company is part of. This value is inherited from the Global Headquarters.


Data Hub API 7.9.0 (2018-11-23)
===============================



Database schema
---------------

- **Companies** The table ``company_companycoreteammember`` was renamed to ``company_onelistcoreteammember``.


Data Hub API 7.8.0 (2018-11-22)
===============================

Deprecations and removals
-------------------------

- **Companies** The API field ``classification`` is deprecated and will be removed on or after November, 29. Please use `one_list_group_tier` instead.
- **Companies** The API field ``one_list_account_owner`` is deprecated and will be removed on or after November, 29. Please use ``GET  /company/<uuid:pk>/one-list-group-core-team`` and get the item in the list with ``is_global_account_manager`` = True instead.
- **Companies** The endpoint ``GET /company/<uuid:pk>/core-team`` is deprecated and will be removed on or after November, 29. Please use ``GET /company/<uuid:pk>/one-list-group-core-team`` instead.
- The API endpoint ``/metadata/company-classification`` is deprecated as not currently necessary. It will be completely removed on or after November, 29.

Internal changes
----------------

- **Investment** The permission ``Can change SPI report (change_spireport)`` was renamed to ``Can view SPI report (view_spireport)`` as Django 2.1 supports view permission and SPI report is read only.

API
---

- **Companies** The field ``classification`` is deprecated and will be removed on or after November, 29. Please use `one_list_group_tier` instead.
- **Companies** The field ``one_list_account_owner`` is deprecated and will be removed on or after November, 29. Please use ``GET  /company/<uuid:pk>/one-list-group-core-team`` and get the item in the list with ``is_global_account_manager`` = True instead.
- **Companies** The One List Core Team endpoint was changed:

  ``GET /company/<uuid:pk>/core-team`` was renamed to ``GET /company/<uuid:pk>/one-list-group-core-team``. The old ``/core-team`` endpoint still exists but will be completely removed on or after November, 29.

  ``GET /company/<uuid:pk>/one-list-group-core-team`` now returns the Core Team for the group that the company is part of. All companies in the group inherit that team from their Global Headquarters.
- **Companies** ``GET /v3/company/<uuid:pk>`` and ``GET /v3/company`` now include the read-only field ``one_list_group_tier`` which is the One List Tier for the group, inherited from the Global Headquarters.
- **Companies** The field `classification` is now read-only in all company endpoints.
- **Investment** ``POST /v3/investment/`` endpoint now accepts ``country_investment_originates_from`` as an
  optional property that can be set whilst creating an investment project.
  The property expects an id of a country.

  ``GET /v3/investment/<uuid:pk>/`` endpoint now includes ``country_investment_originates_from``
  field in the response.

  ``PATCH /v3/investment/<uuid:pk>/`` endpoint now accepts ``country_investment_originates_from``
  as an optional property that can be set whilst updating an investment project.
  The property expects an id of a country.
- The endpoint ``/metadata/company-classification`` is deprecated as not currently necessary. It will be completely removed on or after November, 29.

Database schema
---------------

- **Investment** Column ``country_investment_originates_from`` has been added to ``investment_investmentproject``
  table and is nullable.


Data Hub API 7.7.0 (2018-11-15)
===============================



Features
--------

- **Investment** Exports of search results now include the town or city of the investor company.

Internal changes
----------------

- Countries now have defined ISO codes.
- Django Rest Framework was updated to version 3.9.0.

API
---

- **Investment** ``POST /v3/search/investment_project/export``: the field 'Investor company town or city' was added to the CSV output.


Data Hub API 7.6.0 (2018-11-12)
===============================



Features
--------

- **Companies** A tool for merging duplicate companies was added to the admin site. This tool moves contacts and interactions from one
  company to another, and archives the company that the contacts and interactions were moved from. The tool is
  accessed via a link displayed when viewing a single company (in the admin site). Some limitations exist (for example,
  companies with investment projects or OMIS orders cannot be merged into another company).

Internal changes
----------------

- Various dependencies were updated.


Data Hub API 7.5.0 (2018-11-08)
===============================



Deprecations and removals
-------------------------

- **Advisers** The column ``company_advisor.use_cdms_auth`` was deleted from the database.

Features
--------

- **Investment** First part of the streamlined investment flow. Feature flag ``streamlined-investment-flow`` introduced
  to control when the project manager information is required and to allow the assign pm stage to be deprecated.

Internal changes
----------------

- **Investment** A command ``activate_streamlined_investment_flow`` has been added to active the
  ``streamlined_investment_flow`` feature and update any project at the ``Assign PM`` stage
  to ``Prospect``.
- The ``countries.yaml`` fixture was updated to reflect the current production data.
- It's not possible to change ``Countries`` and ``OverseasRegions`` from the django admin anymore. They will need to be updated using data migrations instead.
- The Elasticsearch Python client libraries were updated to 6.x versions, as was the Docker image used during development.
- A setting to sync updates to records to Elasticsearch using Celery (rather than the thread pool) was adding. This
  will improve performance when many records are updated at once, and increase reliability as failed synchronisation
  attempts are automatically retried. When the setting is enabled, Redis and Celery must be configured and running to
  use endpoints that create or update records.

API
---

- **Investment** ``GET /metadata/investment-project-stage/<uuid:pk>/`` endpoint no longer returns null values
  for field ``exclude_from_investment_flow``. All existing records now return false with
  the exception of 'Assign PM' which returns true.

Database schema
---------------

- **Advisers** The column ``company_advisor.use_cdms_auth`` was deleted from the database.
- **Investment** Column ``exclude_from_investment_flow`` on ``metadata_investmentprojectstage`` table is
  no longer nullable and the default value has been set to False. Existing entries have
  all been updated to False with the exception of 'Assign PM' which has been set to True.
- A new field ``iso_alpha2_code`` was added to the ``metadata_country`` table. It has not been populated yet.


Data Hub API 7.4.0 (2018-11-01)
===============================



Features
--------

- **Companies** Company timeline now includes ``data_source_label`` field that contains human-readable data source description.
- **Companies** New fields named ``transferred_to`` and ``transfer_reason`` have been added to indicate if a company has had its data
  transferred to another record and should no longer be used. The field contains a reference to the company that should
  be used instead. The field cannot be directly changed; it will be set by an upcoming admin tool for merging duplicate
  companies.
- **Investment** A new field ``exclude_from_investment_flow`` has been added to the ``InvestmentProjectStage`` metadata to
  indicate if a stage should be excluded from the investment flow. The field will be used to aid with
  deprecating and adding new stages.

Internal changes
----------------

- Python was updated from version 3.6.6 to 3.6.7 in deployed environments.


API
---

- **Companies** ``GET /v3/company/<uuid:pk>/timeline`` endpoint now includes ``data_source_label`` field in the response. This field contains human-readable data source description.
- **Companies** ``GET,POST /v3/company``, ``GET,POST /v3/company/<id>``: New, optional read-only fields named ``transferred_to`` and
  ``transfer_reason`` have been added to indicate if a company has had its data transferred to another record and should
  no longer be used. When set, this field contains two sub-fields (``id`` and ``name``) which give details of the company
  that should be used instead. The only possible value for transfer_reason at present is ``duplicate``, which indicates
  that it was a duplicate record.

  ``GET,POST /v3/company/unarchive``: It is not possible to unarchive a company that has a value in the ``transferred_to`` field.
- **Investment** ``GET /metadata/investment-project-stage/<uuid:pk>/`` endpoint now includes ``exclude_from_investment_flow``
  field in the response.

Database schema
---------------

- **Companies** A new nullable column ``transferred_to`` has been added to the ``company_company`` table as a foreign key to another company
  record. The column indicates that data about the company has been transferred to another record, and the referenced
  company is the one that should be used instead.

  A new column ``transfer_reason`` has been added to the ``company_company`` table. This indicates the reason that data
  about the company was transferred. The current possible values are an empty string, or ``'duplicate'``.
- **Investment** A new column ``exclude_from_investment_flow`` has been added to the ``metadata_investmentprojectstage`` table.
  The column indicates if the stage should be excluded from the investment flow timeline.


Data Hub API 7.3.0 (2018-10-25)
===============================



Deprecations and removals
-------------------------

- **Advisers** The field ``use_cdms_auth`` is deprecated and will be removed on or after 1 November.
- The table ``leads_businesslead`` was deleted.

Features
--------

- **Interactions** Policy feedback interactions are now always excluded from interaction exports (regardless of the current user's permissions).
- **Investment** SPI report now shows "Project manager first assigned by" (who first time assigned a project manager) column.

Internal changes
----------------

- Various dependencies were updated.

API
---

- **Interactions** ``POST /v3/search/interaction/export`` now always excludes policy feedback interactions (regardless of the current user's permissions).

Database schema
---------------

- **Advisers** The column ``company_advisor.use_cdms_auth`` is deprecated and will be removed on or after 1 November.
- **Investment** The column ``investment_investmentproject.project_manager_first_assigned_by`` has been added. It is nullable and contains a foreign key to the adviser who first time assigned a project manager.
- The table ``leads_businesslead`` was deleted.


Data Hub API 7.2.0 (2018-10-18)
===============================



Deprecations and removals
-------------------------

- All business leads endpoints were removed from the API.

Features
--------

- **Investment** SPI report now shows "Enquiry type" (the type of interaction that triggered the end of SPI1) and "Enquiry processed by" (who has created the interaction) columns.
- When viewing a record in the admin site, a link to the page for the record in the main application is now displayed (when applicable).

Bug fixes
---------

- **Contacts** The speed of the admin site tool for loading marketing email opt-outs was improved via the creation of an additional database index.
- **Investment** Estimated land date is now validated when other required fields are missing.

API
---

- The following endpoints were removed:

  GET,POST /v3/business-leads

  GET,PATCH /v3/business-leads/<uuid:pk>

  POST /v3/business-leads/<uuid:pk>/archive

  POST /v3/business-leads/<uuid:pk>/unarchive


Data Hub API 7.1.0 (2018-10-11)
===============================



Deprecations and removals
-------------------------

- **Contacts** The column ``company_contact.contactable_by_dit`` has been deleted from the database.

  The column ``company_contact.contactable_by_uk_dit_partners`` has been deleted from the database.

  The column ``company_contact.contactable_by_overseas_dit_partners`` has been deleted from the database.

  The column ``company_contact.contactable_by_email`` has been deleted from the database.

  The column ``company_contact.contactable_by_phone`` has been deleted from the database.
- ``GET /whoami/`` no longer returns the ``read_*`` permissions that were being returned for backwards compatibility following the introduction of ``view_*`` permissions.

Internal changes
----------------

- Various dependencies were updated.

API
---

- ``GET /whoami/`` no longer returns the ``read_*`` permissions that were being returned for backwards compatibility following the introduction of ``view_*`` permissions.

Database schema
---------------

- **Contacts** The column ``company_contact.contactable_by_dit`` has been deleted from the database.

  The column ``company_contact.contactable_by_uk_dit_partners`` has been deleted from the database.

  The column ``company_contact.contactable_by_overseas_dit_partners`` has been deleted from the database.

  The column ``company_contact.contactable_by_email`` has been deleted from the database.

  The column ``company_contact.contactable_by_phone`` has been deleted from the database.


Data Hub API 7.0.0 (2018-10-04)
===============================



Deprecations and removals
-------------------------

- **Contacts** The field ``contactable_by_dit`` was removed from the API. The database column will be deleted with the next release.

  The field ``contactable_by_uk_dit_partners`` was removed from the API. The database column will be deleted with the next release.

  The field ``contactable_by_overseas_dit_partners`` was removed from the API. The database column will be deleted with the next release.

  The field ``contactable_by_email`` was removed from the API. The database column will be deleted with the next release.

  The field ``contactable_by_phone`` was removed from the API. The database column will be deleted with the next release.
- Business leads table and endpoints are deprecated. Please check the API and Database schema categories for more details.

Features
--------

- **Interactions** The character limit for the notes field was increased from 4000 to 10,000.

Internal changes
----------------

- The index.mapping.single_type Elasticsearch setting is no longer set to improve compatibility with Elasticsearch 6.x.
- Various dependencies were updated.

API
---

- **Contacts** The field ``contactable_by_dit`` was removed from all contact endpoints.

  The field ``contactable_by_uk_dit_partners`` was removed from all contact endpoints.

  The field ``contactable_by_overseas_dit_partners`` was removed from all contact endpoints.

  The field ``contactable_by_email`` was removed from all contact endpoints.

  The field ``contactable_by_phone`` was removed from all contact endpoints.
- **Interactions** The character limit for the notes field was increased from 4000 to 10000 for the following endpoints:

  ``GET,POST /v3/interaction``

  ``GET,PATCH /v3/interaction/<uuid:pk>``
- The following endpoints are deprecated and will be removed on or after October 11:

  ``GET,POST /v3/business-leads``

  ``GET,PATCH /v3/business-leads/<uuid:pk>``

  ``POST /v3/business-leads/<uuid:pk>/archive``

  ``POST /v3/business-leads/<uuid:pk>/unarchive``

Database schema
---------------

- **Contacts** The column ``company_contact.contactable_by_dit`` was made nullable in preparation for its removal.

  The column ``company_contact.contactable_by_uk_dit_partners`` was made nullable in preparation for its removal.

  The column ``company_contact.contactable_by_overseas_dit_partners`` was made nullable in preparation for its removal.

  The column ``company_contact.contactable_by_email`` was made nullable in preparation for its removal.

  The column ``company_contact.contactable_by_phone`` was made nullable in preparation for its removal.
- The table ``leads_businesslead`` is deprecated and will be removed on or after October 11.


Data Hub API 6.4.0 (2018-09-27)
===============================



Deprecations and removals
-------------------------

- **Companies** The column ``company_company.account_manager_id`` was deleted from the database.

Features
--------

- **Contacts** A list of email addresses to opt out of marketing emails can now be loaded via the admin site.
- URLs in CSV exports and reports are no longer clickable when the CSV file is opened in Excel. This is because the links do not behave correctly when clicked on in Excel (see https://support.microsoft.com/kb/899927 for further information on why).

Bug fixes
---------

- **Companies** The link in the admin site to export the One List was removed from the adviser, Companies House company, contact and export experience category lists. (It still appears on the company list as originally intended.)
- **Investment** Restricted users can now list proposition documents associated to their team's investment projects.

Internal changes
----------------

- **Investment** Deletion of proposition or evidence document is now logged in UserEvent model. UserEvent records can be viewed from the admin site.
- Various dependencies were updated.

Database schema
---------------

- **Companies** The column ``company_company.account_manager_id`` was deleted from the database.


Data Hub API 6.3.0 (2018-09-12)
===============================



Deprecations and removals
-------------------------

- **Companies** The field `account_manager` was removed from the API, from the Django admin and from the model definition. The database column will be deleted with the next release.
- **Contacts** The field ``contactable_by_dit`` is deprecated. Please check the API and Database schema categories
  for more details.

  The field ``contactable_by_uk_dit_partners`` is deprecated. Please check the API and Database schema categories

  The field ``contactable_by_overseas_dit_partners`` is deprecated. Please check the API and Database schema categories
  for more details.

  The field ``contactable_by_email`` is deprecated. Please check the API and Database schema categories
  for more details.

  The field ``contactable_by_phone`` is deprecated. Please check the API and Database schema categories
  for more details.

Features
--------

- **Companies** It's now possible to export company search results as a CSV file (up to a maximum of 5000 results).
- **Contacts** It's now possible to export contact search results as a CSV file (up to a maximum of 5000 results).
- **Investment** It is now possible to upload evidence documents for a given investment project.
- **OMIS** It's now possible to export OMIS order search results as a CSV file (up to a maximum of 5000 results).
- URLs in all CSV exports and reports were made clickable when the CSV file is opened in Excel. This was achieved by using the Excel HYPERLINK() function.
- Existing read-only model views in the admin site were updated to disable the change button
  that previously had no purpose.
- Performed exports of search results are now logged in a new model called UserEvent. UserEvent records can be viewed from the admin site.

Bug fixes
---------

- **Investment** Proposition now needs to have at least one document uploaded in order to be completed.
  It is now optional to provide details when completing a proposition.
  This functionality is behind ``proposition-documents`` feature flag, that needs to be active in order for the new behaviour to work.

API
---

- **Companies** The field `account_manager` was removed from all company endpoints.
- **Companies** ``POST /v3/search/company/export`` was added for exporting company search
  results as a CSV file with up to 5000 rows. The ``company.export_company``
  permission was also added and is required to use this endpoint.
- **Contacts** ``POST /v3/search/contact/export`` was added for exporting contact search
  results as a CSV file with up to 5000 rows. The ``company.export_contact``
  permission was also added and is required to use this endpoint.
- **Contacts** ```GET,POST /v3/contact``` and ```GET,POST /v3/contact/<uuid:pk>``` the fields contactable_by_dit, contactable_by_uk_dit_partners, contactable_by_overseas_dit_partners, contactable_by_email, contactable_by_phone are deprecated and will be removed on or after September 11
- **Investment** ``GET /v3/investment/<investment project pk>/evidence`` gets list of evidence documents.

  ``POST /v3/investment/<investment project pk>/evidence`` creates new evidence document upload.

  ``GET /v3/investment/<investment project pk>/evidence/<evidence document pk>`` gets details of evidence document

  ``DELETE /v3/investment/<investment project pk>/evidence/<evidence document pk>`` deletes given evidence document.

  ``POST /v3/investment/<investment project pk>/evidence/<evidence document pk>/upload_callback`` notifies that file upload has been completed and initiates virus scanning.

  ``GET /v3/investment/<investment project pk>/evidence/<evidence document pk>/download`` returns a signed URL to the document file object.

  Following permissions are required to use the endpoints:

  ``evidence.add_all_evidencedocument``

  ``evidence.view_all_evidencedocument``

  ``evidence.change_all_evidencedocument``

  ``evidence.delete_all_evidencedocument``

  For DA and LEP:

  ``evidence.add_associated_evidencedocument``

  ``evidence.view_associated_evidencedocument``

  ``evidence.change_associated_evidencedocument``

  ``evidence.delete_associated_evidencedocument``
- **OMIS** ``POST /v3/search/order/export`` was added for exporting OMIS order search results as a CSV file with up to 5000 rows. The ``order.export_order`` permission was also added and is required to use this endpoint.

Database schema
---------------

- **Contacts** The column ```contact.contactable_by_dit``` is deprecated and may be removed on or after 11 September.

  The column ```contact.contactable_by_uk_dit_partners```  is deprecated and may be removed on or after 11 September.

  The column ```contact.contactable_by_overseas_dit_partners```  is deprecated and may be removed on or after 11 September.

  The column ```contact.contactable_by_email```  is deprecated and may be removed on or after 11 September.

  The column ```contact.contactable_by_phone```  is deprecated and may be removed on or after 11 September.
- **Investment** New tables ``evidence_evidencedocuments``, ``evidence_evidence_tag`` and ``evidence_evidencedocument_tags`` have been added to enable evidence document upload.
- **Investment** The ``details`` field in ``proposition_proposition`` table can now be blank.
- **Investment** The ``add_associated_investmentproject_proposition`` permission has been renamed to ``add_associated_proposition`` to be consistent with other entities.
- **Investment** The ``change_associated_investmentproject_proposition`` permission has been renamed to ``change_associated_proposition`` to be consistent with other entities.
- **Investment** The ``view_associated_investmentproject_proposition`` permission has been renamed to ``view_associated_proposition`` to be consistent with other entities.
- **Investment** The ``delete_propositiondocument`` permission has been renamed to ``delete_all_propositiondocument`` to be consistent with other entities.
- **Investment** The ``deleted_associated_propositiondocument`` permission has been renamed to ``delete_associated_propositiondocument``.


Data Hub API 6.2.0 (2018-08-23)
===============================



Deprecations and removals
-------------------------

- **Companies** The field ``account_manager`` has been deprecated. Please check the API and Database schema categories
  for more details.
- **Companies** The column ``company_company.parent_id`` has been deleted from the database.
- ``GET /whoami/`` endpoint: ``read_*`` permissions have been renamed to ``view_*``. This endpoint will return both ``view_*`` and ``read_*`` permissions for now but ``read_*`` permissions are deprecated and will soon be removed.

Features
--------

- **Companies** It's now possible to export the one list via the django admin from the company changelist.
- **Interactions** The CSV export of search results has been amended to return various additional columns.
- **Investment** It's now possible to export investment project search results as a CSV file (up to a maximum of 5000 results).
- The format of timestamps in CSV exports and reports was changed to YYYY-MM-DD HH-MM-SS for better compatibility with
  Microsoft Excel.
- Document upload now uses V2 API of AV service.

Bug fixes
---------

- Document upload streaming to AV service now uses a StreamWrapper to encode the file as multipart/form-data in order to send it to AV service. This fixes the problem when the file has been sent incorrectly.

Internal changes
----------------

- Django was updated to version 2.1.

API
---

- **Companies** ``GET,POST /v3/company/<uuid:pk>`` and ``GET /v3/search/company``: the field
  ``account_manager`` has been deprecated and will be removed on or after August 30.
  Please use ``one_list_account_owner`` instead.
- **Interactions** ``GET /v3/interaction`` can now be sorted by ``dit_adviser__first_name``, ``dit_adviser__last_name``, and ``subject``.
- **Investment** ``POST /v3/search/investment_project/export`` was added for exporting investment project search
  results as a CSV file with up to 5000 rows. The ``investment.export_investmentproject``
  permission was also added and is required to use this endpoint.
- ``GET /whoami/`` endpoint: ``read_*`` permissions have been renamed to ``view_*``. This endpoint will return both ``view_*`` and ``read_*`` permissions for now but ``read_*`` permissions are deprecated and will soon be removed.

Database schema
---------------

- **Companies** The column ``company_company.account_manager_id`` has been deprecated and will be removed on or after August 30.
  Please use ``company_company.one_list_account_owner_id`` instead.
- **Companies** The column ``company_company.parent_id`` has been deleted from the database.


Data Hub 6.1.0 (2018-08-15)
===========================

Investment projects
-------------------

-  Added models for evidence documents (endpoints to follow in a future
   release)
-  Fixed a bug in the Celery task for SPI report creation that caused
   the task to fail. (As a result, S3 keys for future reports will no
   longer include the bucket name.)

Search
------

-  Rewrote the mechanism for exporting results to run the search against
   Elasticsearch but extract data from PostgreSQL, and limited the
   number of rows exported to 5000
-  Removed all data exports expect for the interactions one (further
   changes to follow in a future release)


Data Hub 6.0.0 (2018-08-14)
===========================

Companies
---------

-  Removed unused ``parent`` field from the model definition. The
   database column will be deleted from the schema on or after August 21

Contacts
--------

-  Added a management command to update the email marketing status of
   contacts using a CSV file

Investment projects
-------------------

-  Added the ability to upload documents to propositions
-  Removed old document functionality

Internal changes
----------------

-  Stopped using nested Elasticsearch queries
-  Removed the migration path from legacy Elasticsearch single-index
   set-ups
-  Updated various dependencies
-  Updated the test data


Data Hub 5.1.0 (2018-08-02)
===========================

Companies
---------

-  Added a core team member model to hold the advisers in the core team
   for a company
-  Updated the core team endpoint to return advisers from the core team
   member model
-  Improved the layout of the admin page for a company

Miscellaneous
-------------

-  Updated the admin site to display the created on and by and modified
   on and by fields more consistently, and to correctly update those
   fields when changes are made via the admin site

Internal changes
----------------

-  Removed (unused) Elasticsearch alias-related management commands
-  Improved timeout handling during Elasticsearch queries
-  Updated various dependencies


Data Hub 5.0.0 (2018-07-31)
===========================

Companies
---------

-  Added a company core team endpoint at
   ``/v3/company/<company-pk>/core-team`` (currently only returning the
   global account manager)

Internal changes
----------------

-  Moved to one Elasticsearch index per mapping type, and added a
   command (``./manage.py migrate_es``) to migrate Elasticsearch index
   mappings. See `docs/Elasticsearch migrations.md`_ for more detail.
   (After upgrading, ``./manage.py init_es`` must be run to update index
   aliases.)
-  Fixed a random failure in the ``TestListCompanies.test_sort_by_name``
   test
-  Added a contact for an archived company to the test data
-  Updated various dependencies

.. _docs/Elasticsearch migrations.md: https://github.com/uktrade/data-hub-leeloo/blob/master/docs/Elasticsearch%20migrations.md


Data Hub < 5.0.0
================

Please check the `previous releases on GitHub`_.

.. _previous releases on GitHub: https://github.com/uktrade/data-hub-leeloo/releases
