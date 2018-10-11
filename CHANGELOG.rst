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
