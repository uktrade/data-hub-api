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
