# Data Hub API 27.6.0 (2020-02-10)


## Features

- **Companies** The `automatic-company-archive` Celery job will now run with simulation mode turned off.

  We ran this job in simulation mode in order to audit the list of companies that would be archived. This is now done and so we are ready to turn off the simulation.
- **Companies** Formatting of the dnb link admin tool's validation errors were improved by
  splitting them across multiple flash messages.

## Internal changes

- **Companies** A base exception class `DNBServiceError` was added that all dnb-service related
  exceptions inherit.
- **Companies** Duns number validation was standardised to use django's `integer_validator`.

## API

- **Companies** `GET /v4/company-referral`, `POST /v4/company-referral`, `GET /v4/company-referral/<id>`: The following read-only fields were added to responses:

  - `closed_by`
  - `closed_on`
  - `completed_by`


# Data Hub API 27.5.0 (2020-02-06)


## Features

- **Companies** A search app `ExportCountryHistory` was added to expose an API interface to the frontend. The app is supposed to 
  aggregate data from both `CompanyExportCountryHistory` model and related `Interactions` data with the possibility to 
  filter by `country.pk` and `company.pk`. The response should be in descending order by `history_date` datetime.

## Internal changes

- **Companies** Filtering by export countries is now being done with the `CompanyExportcountry` model.

## Database schema

- **Companies** The following columns were added to the `company_referral_companyreferral` table:

  - `"closed_by_id" uuid NULL`
  - `"closed_on" timestamp with time zone NULL`


# Data Hub API 27.4.0 (2020-02-06)


## Bug fixes

- **Companies** It's now possible to execute the export countries migration task in batches.

## API

- **Advisers** `GET /adviser/`: A new query parameter, `permissions__has`, was added. This filters results to 
  advisers with a particular permission.

  For example, `GET /adviser/?permissions__has=company_referral.change_companyreferral` returns
  advisers that are allowed to update company referrals.


# Data Hub API 27.3.0 (2020-02-05)


## Features

- **Companies** A button was added to the admin company change list "Link Company With D&B" which
  puts the D&B link tool live for admin users.
- **Companies** A view was added to allow admin users to review and confirm changes that will 
  be made for D&B company linking.

## API

- **Investment** The `GET /v4/dataset/investment-projects-activity-dataset` has been added. The endpoint returns SPI report records for 
  corresponding investment projects. The response has following fields:
 
    - investment_project_id
    - enquiry_processed
    - enquiry_type
    - enquiry_processed_by_id
    - assigned_to_ist
    - project_manager_assigned
    - project_manager_assigned_by_id
    - project_moved_to_won
    - aftercare_offered_on
    - propositions

      The propositions is an array with following fields:
    
      - deadline
      - status
      - modified_on
      - adviser_id


# Data Hub API 27.2.0 (2020-02-04)


## Features

- **Companies** A view was added to allow admin users to select company ID/duns number for D&B
  company linking. This forms the first step for the admin D&B link tool. As the
  tool is not yet complete, it is not linked to from elsewhere in the admin yet.

## API

- **Companies** The `GET /v4/company/<pk>` API endpoint was updated to make sure `export_countries` field is included in the response only when the user has `company.view_companyexportcountry` permission. And omits otherwise.

  The `PATCH /v4/company/<pk>/export-detail` API endpoint was updated to make sure requests from users with `company.change_companyexportcountry` permission are honoured.
- **Companies** A new endpoint, `GET /v4/company-referral` has been added. It lists referral sent or received by the adviser. 
  Refer to the API documentation for the schema.
- **Companies** A new endpoint, `GET /v4/company-referral/<id>`, was added. This retrieves a single referral object.


# Data Hub API 27.1.0 (2020-02-03)


## Internal changes

- **Companies** The `update_from_dnb` admin tool was refactored to break out some useful utilities
  for use by other modules.  This will aid in the new "Link Company with D&B" tool
  which will follow shortly.
- Some data retention and `dbmaintenance` queries were updated to filter on `Exists()` subqueries directly (rather than via an annotation) following the update to Django 3.0.
- Django was updated from version 2.2.9 to 3.0.3.

## API

- **Companies** A new endpoint `PATCH /v4/company/<pk>/export-detail` was added to allow export related details of a company to be edited, including adding export countries into the new `CompanyExportCountry` model, moving from old company export country fields: `export_to_countries` and `future_interest_countries`.

  If feature flag is OFF, API will work as is updating old fields. And if the feature flag is ON, API will start updating new model instead. In both scenarios, data will be synced across to allow feature flag to be switched ON and OFF when required.


# Data Hub API 27.0.0 (2020-01-29)


## Removals

- **Advisers** `GET /adviser/`: The deprecated `first_name`, `first_name__icontains`, `last_name`, `last_name__icontains`, `email` and `email__icontains` query parameters were removed.

## Features

- **Companies** A utility function `datahub.dnb_api.link_company.link_company_with_dnb` was added which
  provides a mechanism for linking a Data Hub company record with a D&B company
  record. The utility function saves the pertinent D&B data to the Data Hub record.

  This will allow us to firstly provide an admin mechanism for quickly linking
  companies, followed by an API endpoint.
- **Companies** The following criteria were added to the `automatic-company-archive` Celery task:

  - Do not have any ongoing investment projects
  - Do not have any investor profiles

## API

- **Advisers** `GET /adviser/`: The deprecated `first_name`, `first_name__icontains`, `last_name`, `last_name__icontains`, `email` and `email__icontains` query parameters were removed.
- **Companies** A new endpoint, `POST /v4/company-referral`, was added. This creates a new company referral. Refer to the API documentation for the schema.


# Data Hub API 26.6.0 (2020-01-28)


## Features

- **Companies** The `format_dnb_company` now includes a check for `annual_sales_currency`.

  If `annual_sales_currency` is not US Dollars, we do not propagate `annual_sales` or `is_annual_sales_estimated` fields downstream.

  All D&B records that we have encountered until now have `annual_sales` in US dollars but we would like to monitor this behavior and not ingest bad data in case there is an exception.
- **Companies** Added a `datahub.dbmaintenance` command `get_dnb_one_list_tier_companies.py` which
  enables querying of DNB-matched One List Tier B companies. This was re-instated
  after removal in a previous commit to enable further rollout of DNB hierarchies
  to Data Hub company records.

## Database schema

- **Companies** A new `company_referral_companyreferral` table was added to hold referrals of companies between DIT advisers.

  The table has the following columns:

  - `"id" uuid NOT NULL PRIMARY KEY`
  - `"created_on" timestamp with time zone NULL`
  - `"modified_on" timestamp with time zone NULL`
  - `"status" varchar(255) NOT NULL`
  - `"completed_on" timestamp with time zone NULL`
  - `"subject" varchar(255) NOT NULL`
  - `"notes" text NOT NULL`
  - `"company_id" uuid NOT NULL`
  - `"completed_by_id" uuid NULL`
  - `"contact_id" uuid NULL`
  - `"created_by_id" uuid NULL`
  - `"modified_by_id" uuid NULL`
  - `"recipient_id" uuid NOT NULL`


# Data Hub API 26.5.0 (2020-01-27)


## Features

- **Companies** The company list view in Django admin now has a filter for `dnb_modified_on` field.

  This allows us to e.g. filter companies that were updated during today.
- Endpoints are now sorted by path in the API docs.

## Internal changes

- Swagger UI, used in the API docs, was updated to version 3.25.0.

## API

- **Companies** `GET /v4/dataset/companies-dataset`: 2 new fields were added to the companies dataset response:
  - `global_headquarters_id`
  - `global_ultimate_duns_number`
- **Companies** `GET /v4/company/<pk>`: Expose export countries as `export_countries` from new `CompanyExportCountry` model within company response. The field has following structure:

   ```json
  {
      "export_countries": [
          {
          "country": {
              "name": ...,
              "id": ...
          },
          "status": "currently_exporting"
          },
          {
          "country": {
              "name": ...,
              "id": ...
          },
          "status": "not_interested"
          },
          {
          "country": {
              "name": ...,
              "id": ...
          },
          "status": "future_interest"
          },
      ]
  }
  ```
- **Interactions** `GET /v4/dataset/interactions-dataset`: The field `modified_on` was added to the interactions dataset endpoint.


# Data Hub API 26.4.0 (2020-01-20)


## Features

- **Companies** A new Celery task called `automatic_company_archive` was added to Data Hub API.

  This task would run every Saturday at 8pm in *simulation mode* with an upper limit of a *1000 companies*. In simulation mode, this task would log the IDs of the companies that would have been automatically archived using the following criteria:

  - Do not have any OMIS orders
  - Do not have any interactions during the last 8 years
  - Not matched to any D&B records
  - Not created or modified during the last 3 months

## Bug fixes

- The `delete_orphaned_versions` command was modified to select records to be deleted in a fashion that is more 
  efficient in the environment it will run.

## API

- **Companies** `POST /v4/search/company`: The behaviour of the `uk_postcode` filter was modified so that spaces are ignored only if a full postcode is searched for.

  This means that `AB11` and `AB1 1` are now distinct searches (where the former would match e.g. `AB11 1AA` and the latter would match e.g. `AB1 1AA`). (Previously, both searches were equivalent and matched both postcodes.)
- **Interactions** Interactions API `/v3/interaction`, `export_countries` tagged to an interaction are consolidated into `CompanyExportCountry` model, in order to maintain company export countries list. If a country added to an interaction doesn't already exist in company export countries, it will be added. If in case that country already exists, following business rules apply:

  * `Status` of `InteractionExportCountry` added to an interaction with current date overrides the entry within `CompanyExportCountry` with older date.
  * Whereas `Status` of `InteractionExportCountry` added to an interaction with past date can't override the entry within `CompanyExportCountry` with newer date.
  * An interaction added with future date, will be treated as current date and existing rules apply.

## Database schema

- **Companies** A new model `company_companyexportcountryhistory` was created to log all changes made to `company_companyexportcountry` model. This will maintain all inserts, updates and deletions to that model with appropriate `history_type` with values `insert`, `update` and `delete`.


# Data Hub API 26.3.0 (2020-01-15)


## Removals

- The IP restriction functionality provided by `django-admin-ip-restrictor` was removed as it was not in use as we're using private networking and other mechanisms within GOV.UK PaaS instead.

## Features

- It is now possible to perform queries to search endpoints in the API browser.

## Internal changes

- **Investment** The squashed `investor_profile` migration `0001_squashed` was transitioned to a normal migration and the migrations it replaced were removed.

## API

- **Investment** `GET /v4/dataset/investment-projects-dataset`: 5 comma joined string fields were changed to return arrays of strings:
  - `actual_uk_region_names`
  - `business_activity_names`
  - `delivery_partner_names`
  - `strategic_driver_names`
  - `uk_region_location_names`


# Data Hub API 26.2.0 (2020-01-14)

## Removals

- The `dnb_match` app has been removed from Data Hub.

## Internal changes

- `Elasticsearch`: The new `postcode_analyzer` and `postcode_search_analyzer` analyzers were added. Analyzers can be used 
  to enable partial search for area, district, sub-district, sector and a whole postcode. 

  The search is case insensitive and any spaces are filtered out before analysis.
- Uses of the deprecated Django function aliases `force_text()` and `urlquote()` were replaced with `force_str()` and `urllib.parse.quote()`.

## API

- **Companies** `POST /v4/search/company`: A `uk_postcode` filter was added for the `address_postcode` and `registered_address_postcode` 
  fields for UK based companies. The filter accepts a single or a partial postcode as well as an array of postcodes. 
  Multiple postcodes are matched with `or` query.
- **Interactions** `GET /v4/dataset/interactions-dataset`: 3 new fields were added to the interactions dataset response:
  - `policy_area_names`
  - `policy_feedback_notes`
  - `policy_issue_type_names`
- **Interactions** Interactions API `/v3/interaction` now allows to specify if there was a discussion of countries during the interaction and add one or more export countries along with their status.

  `were_countries_discussed` is a nullable boolean field.

  `export_countries` field is of type `InteractionExportCountry` and takes a list of `country` and `status` combinations where `country` is of type `Country` and `status` is a choice of `Not interested`, `Currently exporting to` or `Future country of interest`.

  * Above details are only valid for non-investment themed interactions. Hence `were_countries_discussed` is mandatory field for both `export` and `other` themed interactions.
  * At least one country/status combination is mandatory if `were_countries_discussed` is set to True


# Data Hub API 26.1.0 (2020-01-09)


## API

- **Advisers** `GET /v4/company-list/<pk>/item`: The latest interaction of each list item now includes an array of DIT participants in the `dit_participants` field. In context, the field has the following structure:

  ```json
  {
      "results": [
          {
              "latest_interaction": {
                  "dit_participants": [
                      {
                         "adviser": {
                             "id": ...,
                             "name": ...
                         },
                         "team": {
                             "id": ...,
                             "name": ...
                         }
                      },
                      ...
                  ]
              }
          }
      ]
  }
  ```


# Data Hub API 26.0.0 (2020-01-08)


## Removals

- The following deprecated endpoints have been removed from Data Hub API:

  - `GET v4/dnb-match/<uuid:company_pk>`
  - `POST v4/dnb-match/<uuid:company_pk>/select-match`
  - `POST v4/dnb-match/<uuid:company_pk>/select-no-match`
- The following deprecated tables have been removed from Data Hub API:

  - dnb_match_dnbmatchingcsvrecord
  - dnb_match_dnbmatchingresult

## Features

- **Companies** The `datahub.dnb_api.tasks.get_company_updates` task now run with a specific list of fields to update by default.

  This was introduced to not update `domain` & `registered_address` fields. This is because the data for these fields does not meet Data Hub standards. D&B have been informed of this and are working on a fix.

- Python was updated from version 3.7.5 to 3.8.1. This includes updating various indirect dependencies.

## Internal changes

- The following internal query utilities were added:

  - `get_array_agg_subquery()`
  - `JSONBBuildObject`

## API

- **Investment** `GET /v4/dataset/investment-projects-dataset`: The `allow_blank_possible_uk_regions` field was removed and replaced with `uk_region_location_names`.


# Data Hub API 25.0.0 (2020-01-02)


## Removals

- **Companies** The feature flag that enabled the new add-a-company journey was removed.

  This makes the new add-a-company journey the default way to add a new company in Data Hub.
- **Companies** The `get_dnb_one_list_tier_companies` management command was removed from Data Hub.

  This command was put in temporarily to safely run queries required for DNB company hierarchies rollout.

## Deprecations

- The following `dnb-match` endpoints will be deprecated on or after 5 January 2020:

  - `GET v4/dnb-match/<uuid:company_pk>`
  - `POST v4/dnb-match/<uuid:company_pk>/select-match`
  - `POST v4/dnb-match/<uuid:company_pk>/select-no-match`
- The following tables will be removed from Data Hub on or after 5 Jan 2020:

  - `dnb_match_dnbmatchingcsvrecord`
  - `dnb_match_dnbmatchingresult`


# Data Hub API 24.5.0 (2019-12-23)


## Features

- **Companies** Added integration tests for the `rollback_dnb_company_updates` management command.
  This can now be used as it has been fully tested.
- **Companies** A management command `rollback_dnb_company_updates` was added to revert updates applied
  by either the `update_company_dnb_data` command or the `get_company_updates` task. 
  At present, the rollback command calls a stub function which will be fleshed out later -
  it is not ready for use.

## Bug fixes

- **Companies** A bugfix was made to ensure that the task id for the overall company updates
  process is used as an update descriptor in reversion comments.  This will allow the use
  of a rollback tool in the event that D&B updates need to be undone.


# Data Hub API 24.4.0 (2019-12-20)


## Features

- **Companies** A new management command, `update_company_uk_region`, was added.

  This can update the UK regions of companies using a CSV file stored in Amazon S3.
- **Companies** A new management command, `update_company_sector`, was added.

  This can update the sectors of companies using a CSV file stored in Amazon S3.


# Data Hub API 24.3.0 (2019-12-19)


## Features

- **Companies** The `update_company_dnb_data` command was adjusted so that an audit log is fired
  to sentry after a successful run.


# Data Hub API 24.2.1 (2019-12-18)


## Bug fixes

- **Companies** A bug was fixed that resulted in a runtime error in the `get_company_updates` celery task.

  The error happened when `get_company_updates` tried to wait on the results of sub-tasks in order to produce an audit log.


# Data Hub API 24.2.0 (2019-12-17)


## Features

- **Companies** A schedule was added for a nightly run of the celery task: `datahub.dnb_api.tasks.get_company_updates`.

  This task will ingest D&B updates from `dnb_service`. The number of updates applied in a single run will be controlled by the environment variable called `DNB_AUTOMATIC_UPDATE_LIMIT`.


# Data Hub API 24.1.0 (2019-12-17)


## Features

- **Companies** Companies updated with the `update_company_from_dnb` command and the 
  `update_companies_from_dnb_service` task are now saved with a reversion version
  which has a meaningful identifier in the comment. This identifier will help provide
  the groundwork for an "undo tool" which will allow us to reverse these automatic
  updates in the event of a problem.
- The CSRF token is now being added to API Docs request header. It is now possible to try POST requests.

## Internal changes

- **Companies** We are now recording `future_interest_countries` 
  and `export_to_countries` with both the `Company` model and the new model `CompanyExportCountry` 
  which we're currently integrating.
- **Investment** All `investor_profile` app database migrations were squashed. The old migrations will be removed once the squashed migration has been applied to all environments.
- The Elasticsearch suggester query parameter `contexts` is now used instead of the deprecated `context` parameter.


# Data Hub API 24.0.0 (2019-12-10)


## Removals

- **Investment** The following deprecated investor profile tables were removed:

  - `investor_profile_investorprofile_asset_classes_of_interest`
  - `investor_profile_investorprofile_construction_risks`
  - `investor_profile_investorprofile_deal_ticket_sizes`
  - `investor_profile_investorprofile_desired_deal_roles`
  - `investor_profile_investorprofile_investment_types`
  - `investor_profile_investorprofile_other_countries_being_cons84de`
  - `investor_profile_investorprofile_restrictions`
  - `investor_profile_investorprofile_time_horizons`
  - `investor_profile_investorprofile_uk_region_locations`
  - `investor_profile_investorprofile`
  - `investor_profile_profiletype`

## Features

- **Companies** A setting `DNB_AUTOMATIC_UPDATE_LIMIT` was added which can be used to limit the
  number of companies updated by the `datahub.dnb_api.tasks.get_company_updates`
  task.
- **Companies** Info log messages and a sentry-based audit log were added to the DNB company
  updates tasks to help provide better visibility for task runs.
- **Companies** A feature flag was added `"dnb-company-updates"` which governs whether or not to
  run the logic within the `datahub.dnb_api.tasks.get_company_updates` celery task.
  This affords us the ability to easily switch on/off DNB company updates as needed 
  during the rollout of this feature.

## Bug fixes

- **Companies** A bug was fixed to ensure that DNB company updates can be ingested over multiple
  pages from dnb-service.  Previously, the cursor value was not being extracted
  from the URL for the next page correctly.

## Internal changes

- **Companies** Integration tests were added for the `datahub.dnb_api.tasks.get_company_updates` task.
  These were not added as part of the original development as the task and it's dependent
  task (`datahub.dnb_api.tasks.update_company_from_dnb_data`) were developed in parallel.

  Additionally, the calls that `datahub.dnb_api.tasks.get_company_updates` makes to
  `datahub.dnb_api.tasks.update_company_from_dnb_data` were fixed to be the correct
  signature.
- Python was updated from version 3.7.4 to 3.7.5 in deployed environments.

## Database schema

- **Interactions** A new table `interaction_interactionexportcountry` was created.
  It has foreign key fields `interaction_id` and `country_id`
  with status, value is expressed as:
  * 'currently exporting to'
  * 'future interest'
  * 'not interested'


# Data Hub API 23.2.0 (2019-12-02)


## Features

- **Companies** A celery task was added which takes a dictionary of company data sourced from
  dnb-service and updates the company record corresponding to it in Data Hub.
- A celery task called `get_company_updates` was added.

  This task gets all the available company updates from the dnb-service and spawns downstream tasks to apply these updates to D&B matched company records in Data Hub.
- The views that will replace stock Django Admin method of authentication with Staff SSO were added.

## Bug fixes

- **Companies** Merging two companies (via the admin site) now works when both companies are on the same company list.

## Internal changes

- We are now exposing  `CSRF_COOKIE_SECURE` and `CSRF_COOKIE_HTTPONLY` Django settings 
  via environment variables.
- The squashed `metadata` app migration `0001_squashed_0010_auto_20180613_1553` was transitioned to a normal migration and the migrations it replaced were removed.

## API

- **Investment** `GET /v4/dataset/investment-projects-dataset`: The `competing_countries` field was updated to return country names rather than ids
- **OMIS** `GET /v4/dataset/omis-dataset`: The field `quote__accepted_on` was added to the omis dataset endpoint


# Data Hub API 23.1.0 (2019-11-28)


## Removals

- The `init_es` management command has been removed. Please use `migrate_es` instead.

## Features

- The `migrate_es` management command was updated to handle the case when indexes don‘t already exist.

  Hence, the `init_es` command is no longer required and has been removed.

## Internal changes

- **Companies** The squashed `company` app migration `0001_squashed_0096_company_global_ultimate_duns_number` was transitioned to a normal migration and the migrations it replaced were removed.
- **Investment** The squashed `investment` app migration `0001_squashed_0068_remove_interaction_location_from_database` was transitioned to a normal migration and the migrations it replaced were removed.

## Database schema

- **Companies** A new table `company_companyexportcountry` was created to maintain company's export interests. Multiple countries along with a status can be recorded for each company. Status being one of `not_interested`, `future_interest` or `currently_exporting`. This will now allow, for each entry, to record date and adviser that created and modified for audit.


# Data Hub API 23.0.0 (2019-11-22)


## Removals

- **Advisers** The `company_list_companylist` column `is_legacy_default` has been removed from database.

## Features

- **Companies** Error handling was added for when a `ConnectionError` occurs when accessing the
  DNB company search API endpoint.

## Internal changes

- **Companies** A temporary management command `get_dnb_one_list_tier_companies` was added to enable the running
  of safe queries to facilitate the rollout of DNB company hierarchies.

## Database schema

- **Advisers** The `company_list_companylist` column `is_legacy_default` has been removed from database.


# Data Hub API 22.0.0 (2019-11-21)


## Removals

- **Companies** The deprecated model `CompaniesHouseCompany` was removed.

## API

- **Companies** `GET /v4/dataset/companies-dataset`: 5 new fields were added to the companies dataset response:
  - `archived`
  - `archived_on`
  - `headquarter_type__name`
  - `modified_on`
  - `one_list_account_owner_id`
- **Contacts** `GET /v4/dataset/contacts-dataset`: 3 new fields were added to the contacts dataset response:
  - `archived`
  - `archived_on`
  - `modified_on`
- **Interactions** `GET /v4/dataset/interactions-dataset`: The field `theme` was added to the interactions dataset api response
- **Investment** `GET /v4/dataset/investment-projects-dataset`: 5 new fields were added to the investment projects dataset api response:
  - `address_1`
  - `address_2`
  - `address_town`
  - `address_postcode`
  - `other_business_activity`
- **OMIS** `GET /v4/dataset/omis-dataset`: 5 new fields were added to the OMIS dataset api response:
  - `quote__created_on`
  - `refund_created`
  - `refund_total_amount`
  - `total_cost`
  - `vat_cost`

## Database schema

- **Advisers** The `company_list_companylist` column `is_legacy_default` has been made nullable and will be removed 
  in the next release.
- **Companies** The deprecated `company_companieshousecompany` table was removed.


# Data Hub API 21.1.0 (2019-11-19)


## Features

- **Investment** A management command `update_investment_project_status` was added which can update the statuses of a list of investment projects from a CSV file stored in Amazon S3.

## API

- **Companies** A field called `dnb_modified_on` was added to the response of the following endpoints:

  - `GET /v4/company`
  - `GET /v4/company/<company_id>`

  This fields tracks the last time a company was updated from D&B.

## Database schema

- **Companies** A field called `dnb_modified_on` was added to the `company_company` table.

  This fields tracks the last time a company was updated from D&B.


# Data Hub API 21.0.0 (2019-11-18)


## Removals

- The deprecated `GET /dashboard/homepage/` endpoint was removed.

## Features

- **Companies** A command was added `datahub.dbmaintenance.management.commands.update_companies_dnb_data`
  which allows us to update the DNB data for a list of company IDs. All Company fields
  are updated by default, but a subset of fields can be specified if a partial update
  is preferable.

## Internal changes

- **Investment** All `investment` app database migrations were squashed in order to reduce build times. The old migrations will be removed once the squashed migration has been applied to all environments.
- All `metadata` app database migrations were squashed in order to reduce build times. The old migrations will be removed once the squashed migration has been applied to all environments.

## API

- **Companies** `GET /v4/dataset/company-export-to-countries-dataset`: An API endpoint for a dataset of export_to_countries was added for consumption by data-flow and data-workspace.


# Data Hub API 20.0.0 (2019-11-14)


## Removals

- **Advisers** The `company_list_companylistitem` column `adviser_id` has been removed from database.
- **Companies** The following deprecated endpoint has been removed:

   - `POST /v4/company`
- **Investment** The deprecated `GET /v3/investment/from` endpoint was removed.

## Features

- The names of various countries were updated to match DIT reference data.

## Internal changes

- **Companies** Database migrations up to 0096 were squashed in order to reduce build times. The old migrations will be removed once the squashed migration has been applied to all environments.

## Database schema

- **Advisers** The `company_list_companylistitem` column `adviser_id` has been removed from database.


# Data Hub API 19.0.0 (2019-11-11)


## Removals

- **Companies** The following deprecated endpoints have been removed:

  - `GET /ch-company`
  - `GET /ch-company/<ch-company-id>`
- **Companies** The following deprecated Comapnies House search endpoints have been removed from Data Hub:

  - `GET /v3/search/companieshousecompany`
  - `GET /v4/search/companieshousecompany`
- **Companies** The `uppdate_company_registered_address` Django command is no longer available in Data Hub.

  This command was used to sync company registered addresses with Companies House data. We have now moved to D&B as the source for company data.

## Internal changes

- **Companies** A celery task `datahub.dnb_api.tasks.sync_company_from_dnb` was added which gives
  a mechanism for syncing specified fields for a DNB-matched company with the latest
  DNB data for that company.


# Data Hub API 18.0.0 (2019-11-08)


## Removals

- **Advisers** The `company_list_companylistitem` column `adviser_id` will be removed in the next release.
- **Advisers** The following legacy company list endpoints were removed:

    - `GET /v4/user/company-list`
    - `GET /v4/user/company-list/<company ID>`
    - `PUT /v4/user/company-list/<company ID>`
    - `DELETE /v4/user/company-list/<company ID>`
- **Companies** The Companies House admin view is no longer available in Data Hub.
- **Companies** The `sync_ch` Django command is no longer available in Data Hub.

  This command was used to sync Companies House data to Data Hub. We have now moved to D&B as the source for company data.

## Deprecations

- **Advisers** A `company_list_companylist` field `"is_legacy_default" boolean NOT NULL` will be removed on or after 20th November.
- **Companies** The following table will be removed from Data Hub on or after 12 November 2019:

  - `company_companieshousecompany`
- **Companies** The following Company endpoint is deprecated and will be removed on or after 12 November 2019:

  - `POST /v4/company`

  DataHub has moved to using D&B creating new companies and so instead of the above endpoint, please use:

  - `POST /v4/dnb/company-create`
- **Investment** The `GET /v3/investment/from` endpoint is deprecated and will be removed on or after 13 November 2019.

  (This was used by the old FDI dashboard which has now been decommissioned.)
- The `GET /dashboard/homepage/` endpoint is deprecated and will be removed on or after 13 November 2019.

  (This was used for the Data Hub home page before the My companies feature.)

## Bug fixes

- **Companies** The `POST /v4/company/<ID>/self-assign-account-manager` and `POST /v4/company/<ID>/remove-account-manager` endpoints now correctly update the `modified_by` field of the company (instead of leaving it unchanged).

## Internal changes

- **Companies** A helper function for the "Update from DNB" admin feature was refactored as
  a utility function `datahub.dnb_api.utils.update_company_from_dnb`.  The function
  can optionally take an iterable of fields to update so that we can partially
  update companies from DNB.
- **Interactions** The squashed migration `0001_squashed_0068_remove_interaction_location_from_database` was transitioned to a normal migration and the migrations it replaced were removed.
- Elasticsearch mapping type migrations are now automatically run during deployments.

## API

- **Companies** `GET /v4/dataset/companies-future-interest-countries-dataset`: An API endpoint for a dataset of future interest countries was added for consumption by data-flow and data-workspace.
- **Companies** `POST /v4/search/company`: A filter was added for the `latest_interaction_date` field, in the form of `latest_interaction_date_before` and `latest_interaction_date_after`. Both the fields are optional. A company will only be returned if its latest interaction date falls between those dates.
- **Contacts** `GET /v4/dataset/contacts-dataset`: The primary contact flag and contact address details were added to the contacts dataset response
- **Events** A new events dataset endpoint (`GET /v4/dataset/events-dataset`) was added to be consumed by data-flow and used in data-workspace.
- **Investment** The following endpoint was added:
  - `GET /v4/dataset/investment-projects-dataset`: Present agreed partially denormalized data of all investment projects to be consumed by data-flow and used in data-workspace for reporting and analyst access.


# Data Hub API 17.1.0 (2019-10-30)


## Deprecations

- **Advisers** The following legacy company list endpoints are deprecated and will be removed on or after 6 November 2019:

  - `GET /v4/user/company-list`
  - `GET /v4/user/company-list/<company ID>`
  - `PUT /v4/user/company-list/<company ID>`
  - `DELETE /v4/user/company-list/<company ID>`

  Please use the new multi-list endpoints starting with `/v4/company-list` instead.
- **Companies** The following Comapnies House endpoints are deprecated and will be removed on or after 6 November 2019:

  - `GET /v4/ch-company`
  - `GET /v4/ch-company/<company_number>`
- **Companies** The following Comapnies House endpoints are deprecated and will be removed on or after 6 November 2019:

  - `GET /v3/search/companieshousecompany`
  - `GET /v4/search/companieshousecompany`

## Features

- **Companies** The `update-from-dnb` admin tool now shows changes to `global_ultimate_duns_number` field in the "review changes" table.
- **Investment** The proposition documents feature is now always active and is no longer behind a feature flag. (This feature was introduced in September 2018.)

## Internal changes

- **Interactions** Database migrations up to 0068 were squashed in order to reduce build times. The old migrations will be removed once the squashed migration has been applied to all environments.
- A correction was made to the deleted object collector (used to delete objects from Elasticsearch in bulk) to make it safe to use in web processes. This change has no current effect as the collector has only been used in management commands to date.
- The speed of search tests was improved by using more efficient test set-up. The reduction in running time of the search tests is approximately 65%.
- Various indirect dependencies were updated.

## API

- **Companies** `POST /v4/search/company`: new filter `one_list_group_global_account_manager` was added.
- **Companies** `GET /v4/dataset/companies-dataset`: The field `address_country__name` was added to the companies dataset endpoint
- **Companies** A new endpoint, `POST /v4/company/<ID>/remove-account-manager`, was added. 

  The endpoint removes the assigned tier and account manager for a One List company on tier 'Tier D - Interaction Trade Adviser Accounts'.

  If the company is on a One List tier other than 'Tier D - Interaction Trade Adviser Accounts', the operation is not allowed.

  The `company.change_company` and `company.change_regional_account_manager` permissions are required to use this endpoint.


# Data Hub API 17.0.0 (2019-10-24)


## Features

- **Companies** A new dbmaintenance Django command was added to import data from csv format, with three fields `datahub_company_id`, `is_published_find_a_supplier` and `has_find_a_supplier_profile` provided by Data Science platform, into Data Hub company model's field, `great_profile_status`.

## Bug fixes

- **Companies** The dbmaintenance command `update_company_export_potential` is fixed to disable search signal receivers for company, to avoid queuing huge number of Celery tasks for syncing companies to Elasticsearch.

## Internal changes

- **Companies** A property `is_global_ultimate` was added to the `Company` model - this exposes
  whether or not a company is the global ultimate.

## API

- **Advisers** A new dataset endpoint (`GET /v4/dataset/advisers-dataset`) was added to be consumed by data-flow and used in data-workspace.
- **Advisers** A new teams dataset endpoint (`GET /v4/dataset/teams-dataset`) was added to be consumed by data-flow and used in data-workspace.
- **Companies** The property `is_global_ultimate` (a boolean) was added as a field to the following company API
  endpoints as a read-only field:

  - `GET /v4/company`
  - `POST /v4/company` - returned in the result
  - `GET /v4/company/<pk>`
  - `POST /v4/dnb/company-create`
- **Companies** The field `global_ultimate_duns_number` was added to the `DNBCompanySerializer`.

  This means that the `global_ultimate_duns_number` returned in the D&B responses will now be saved
  to the `global_ultimate_duns_number` field on the `Company` model.
- **Companies** A new endpoint, `POST /v4/company/<ID>/self-assign-account-manager`, was added. It:

  - sets the authenticated user as the One List account manager
  - sets the One List tier of the company to 'Tier D - Interaction Trade Adviser Accounts'

  The operation is not allowed if:

  - the company is a subsidiary of a One List company (on any tier)
  - the company is already a One List company on a different tier (i.e. not 'Tier D - Interaction Trade Adviser Accounts')

  The `company.change_company` and `company.change_regional_account_manager` permissions are required to use this endpoint.
- **Companies** A filter was added to the company collection API to allow callers to filter by
  `global_ultimate_duns_number` - e.g. `GET /v4/company?global_ultimate_duns_number=123456789`.
- **Companies** The field `global_ultimate_duns_number` was added to the response of the following company API
   endpoints:

  - `GET /v4/company`
  - `GET /v4/company/<pk>`
  - `POST /v4/dnb/company-create`
- **Contacts** `GET /v4/dataset/contacts-dataset`: Company and contact id fields were added to the contacts dataset endpoint 
  `GET /v4/dataset/contacts-dataset`: Superfluous company detail fields were removed from the contacts dataset endpoint
- **Interactions** `GET /v4/dataset/interactions-dataset`: Interaction id was added to the interaction dataset endpoint
- **OMIS** `GET /v4/dataset/omis-dataset`: Join between order and company was removed from the omis dataset endpoint
  `GET /v4/dataset/omis-dataset`: Join between order and contact was removed from the omis dataset endpoint
  `GET /v4/dataset/omis-dataset`: Order id, company id and contact id were added to the omis dataset endpoint
  `GET /v4/dataset/omis-dataset`: Team name was replaced with team id on the omis dataset endpoint

## Database schema

- **Companies** The `company_company` table now contains `global_ultimate_duns_number` field. This field will be populated by the `duns_number` for the global ultimate of a company. This data is included in the D&B payload.


# Data Hub API 16.0.0 (2019-10-21)


## Removals

- The legacy `GET /metadata/*` endpoints were removed. Please use Hawk authenticated `GET /v4/metadata/*` endpoints instead.

## Features

- **Companies** A new dbmaintenance Django command was added to import data from csv format, with two fields `datahub_company_id` and `export_propensity` provided by Data Science platform, into Data Hub comapany model.

## Bug fixes

- Unset cursor pagination `offset_cutoff` on dataset endpoints to fix issue when duplicate `created_on` dates are encountered.

## API

- **Companies** The `GET /company/<uuid:pk>` endpoint's read-only field `one_list_group_global_account_manager` now includes the account manager's contact email address under the `contact_email` field.
- **Companies** `GET /v4/company/<id>`: A new read-only field was added to company model `great_profile_status`. Values for this field are imported from Data Science platform, as a separate exercise. It can have one of the constant values out of `published`, `unpublished` and `null`.
- **Companies** Each adviser object returned by `/v4/company/<uuid:pk>/one-list-group-core-team` endpoint now includes a contact email address under the `contact_email` field.

## Database schema

- **Companies** A nullable `great_profile_status` varchar(255) column was added to the company_company table with possible values 'published', 'unpublished' and NULL.


# Data Hub API 15.9.0 (2019-10-17)


## Internal changes

- **Interactions** Various search model fields that were not being used in search queries (i.e. searched, filtered or sorted) are no longer indexed. This improves indexing performance.


# Data Hub API 15.8.0 (2019-10-14)


## Features

- **Companies** A new permission, `change_regional_account_manager`, was added. This permission currently has no effect and will be used as part of upcoming functionality.

  In the test data, this permission is assigned to teams with the `International Trade Team` role.
- **Companies** A tool was added to django admin to allow administrators to pull fresh data from DNB for a company with a `duns_number`.

  This allows administrators to resolve the unhappy-path for the new add-a-company journey by adding a `duns_number` to a company record followed by pulling data from DNB for the given company.

## Internal changes

- Migrations for the `mi` database are now applied automatically during deployments.


# Data Hub API 15.7.0 (2019-10-11)


## Features

- **Investment** The rounding of `gross value added` now always rounds up rather than using bankers' rounding where it would round to the nearest even number.

## Internal changes

- The IP check that is being used with Hawk authenticated endpoints was enhanced with additional rules to allow traffic 
  originating from an internal network.


# Data Hub API 15.6.0 (2019-10-10)


## Features

- **Companies** A new One List tier was added:
 
  | ID | Name |
  | --- | --- |
  | `1929c808-99b4-4abf-a891-45f2e187b410` | Tier D - International Trade Adviser Accounts |

  This tier currently contains no companies; it will be used as part of upcoming functionality.
- **Companies** Various superfluous unused One List tiers were manually removed from all environments.
- **Companies** All One List tiers were renamed:

  | Old name | New name |
  | --- | --- |
  | Tier A - Strategic Account | Tier A - SRM Programme Accounts |
  | Tier A2 - Global Partners | Tier A - SRM Commercial Partner Accounts |
  | Tier B - Global Accounts | Tier B - Sector Team Accounts |
  | Tier B - Global Accounts (Capital Investment) | Tier B - Capital Investment Team Accounts |
  | Tier C - Local Accounts (UKTI Managed) | Tier C - Investment Services Team Accounts |
  | Tier D - POST Identified/Managed | Tier D - Overseas Post Accounts |
  | Tier D - LEP Managed Branch (not IST) | Tier D - Local Enterprise Partnership Accounts |

## API

- **Interactions** `GET /v4/dataset/interactions-dataset`: Added interactions dataset endpoint to be consumed by data-flow and used in data-workspace.


# Data Hub API 15.5.0 (2019-10-08)


## Features

- **Companies** New fields for `Countries exported to` and `Countries of interest` have been added to the csv file resulting from document download.

## API

- **Companies** `GET /v4/dataset/companies-dataset`: Added companies dataset endpoint to be consumed by data-flow and used in data-workspace.
- **Companies** `GET /v4/company/<id>`: A new read-only field was added to company model `export_potential`. Values for this field are imported from Data Science platform, as a seperate exercise. It can have one of the constant values out of `very_higb`, `high`, `medium`, `low`,`very_low` and `null`.
- The `POST /v4/dnb/company-create` API endpoint will now save `registered_address_*`
  fields on Data Hub companies that it creates. Registered address fields will not be
  saved at all unless a minimum of `line_1`, `town` and `country` fields are provided.


# Data Hub API 15.4.0 (2019-10-03)


## Internal changes

- **Companies** Some intermittently failing company autocomplete tests were corrected so that they now consistently pass.

## API

- **Companies** `POST /v4/search/company`: A filter was added for the `export_to_countries` field. This accepts a list of country IDs. A company will only be returned if it contains one of the specified countries in this field.
- **Companies** `POST /v4/search/company`: A filter was added for the `future_interest_countries` field. This accepts a list of country IDs. A company will only be returned if it contains one of the specified countries in this field.


# Data Hub API 15.3.0 (2019-10-01)


## Features

- **Companies** A tool was added to django admin to allow administrators to "unarchive" archived
  companies.
- A configurable blacklist was added so that we can specifically prohibit certain
  email addresses from the email ingestion feature.
- Email ingestion was adjusted so that emails are deleted after they are ingested.
  Previously, email ingestion would mark the emails as "seen" but now that we are
  out of the pilot for meeting invite ingestion we have switched to deletes as this
  is safer for data retention/protection reasons.
- The email ingestion whitelist was removed so that email ingestion is open to
  all DIT advisers.  
  The email domain that a DIT adviser uses to send an email to Data Hub must be 
  known to Data Hub through a `DIT_EMAIL_DOMAIN_<domain>` django setting -
  there is no longer a default domain authentication value. This ensures that 
  email ingestion is locked down to domains that we know the authentication
  signature for.


# Data Hub API 15.2.0 (2019-09-26)

## Removals

  - **Interactions** The `location` column was removed from the `interaction_interaction` DB table.

## Bug fixes

  - Fixed a bug in the DNB company save API endpoint which prevented DNB companies with no value for <span class="title-ref">domain</span> being saved as Data Hub companies.

## Internal changes

  - **Contacts** Dataset app is split up into subpackages. i.e. datahub.dataset.views to datahub.dataset.contact.views

  - **OMIS** Dataset app is split up into subpackages. i.e. datahub.dataset.views to datahub.dataset.order.views

  - The PaaS IP checks have been removed from Hawk authorisation code. A separate authentication class to check the IP has been implemented instead.
    
    The PaaS IP check can now be disabled using `DISABLE_PAAS_IP_CHECK` environment variable.

## Database schema

  - **Companies** Composite index (created\_on, id) is defined on Contact model for the sake of API endpoints defined under dataset app.
  - **Interactions** The `location` column was removed from the `interaction_interaction` table.

# Data Hub API 15.1.0 (2019-09-19)

## Removals

  - **Interactions** The `location` field for interactions was removed following its deprecation period. Please see the API and DB sections for further detail.

## Features

  - **Companies** A feature was added to notify a configurable list of recipients when a company is added to Data Hub which has the `pending_dnb_investigation` flag set. The intention is for this to be used to send investigation details to DNB directly; though notifications will be monitored with a DIT email address to begin with.

## API

  - **Companies** Two metdata API endpoints were added for One List Tiers. `GET /metadata/one-list-tier/` and `GET /v4/metadata/one-list-tier` list all One List Tier models in the following format:
    
        [
            {
                "id": "b91bf800-8d53-e311-aef3-441ea13961e2",
                "name": "Tier A - Strategic Account",
                "disabled_on": null
            },
            ...,
        ]

  - **Interactions** The `location` field was removed from the `GET /v3/interaction` and `GET /v3/interaction/<uuid:pk>` API endpoints.

  -   - **OMIS** The following API endpoint is updated
        
          - `GET /v4/dataset/omis-dataset`: The sector\_\_segment field was removed and sector\_name was added which is a string of multiple sector names separated by ",".

## Database schema

  - **Interactions** The `location` field was removed from the django state for the `Interaction` model.

# Data Hub API 15.0.0 (2019-09-17)

## Removals

  - **Contacts** `POST /v3/search/contact`, `POST /v3/search/contact/export` various deprecated `sortby` values were removed. See the API section for more details.
  - **Investment** `POST /v3/search/investment_project`, `POST /v3/search/investment_project/export` various deprecated `sortby` values were removed. See the API section for more details.
  - All `/metadata/*` endpoints are deprecated and will be removed on or after 17th October 2019. Please use corresponding `/v4/metadata` endpoints instead.

## Internal changes

  - The `dnb_api` package now has a `DNBCompanyInvestigationSerializer`.
    
    This is used to store stub companies in the database when users cannot find a company in the DNB API and want to create a new company subject to DNB review.

## API

  - **Companies** The `GET /v4/company` and `GET /v4/company/<uuid:pk>` endpoints were modified to return the boolean `pending_dnb_investigation` in responses. The format of the responses are as follows:
    
        "pending_dnb_investigation": true,

  - **Contacts** The following endpoint was added:
    
      - `GET /v4/dataset/contacts-dataset`: Present required fields data of all contacts to be consumed by data-flow and used in data-workspace for reporting and analyst access.

  - **Contacts** `POST /v3/search/contact`, `POST /v3/search/contact/export` the following deprecated `sortby` values were removed:
    
      - `accepts_dit_email_marketing`
      - `address_county`
      - `address_same_as_company`
      - `address_town`
      - `adviser.name`
      - `archived`
      - `archived_by.name`
      - `archived_on`
      - `company_sector.name`
      - `email`
      - `first_name`
      - `id`
      - `job_title`
      - `name`
      - `primary`
      - `telephone_countrycode`
      - `telephone_number`
      - `title.name`

  - **Investment** `POST /v3/search/investment_project`, `POST /v3/search/investment_project/export` the following deprecated `sortby` values were removed:
    
      - `actual_land_date`
      - `approved_commitment_to_invest`
      - `approved_fdi`
      - `approved_good_value`
      - `approved_high_value`
      - `approved_landed`
      - `approved_non_fdi`
      - `archived`
      - `archived_by.name`
      - `average_salary.name`
      - `business_activities.name`
      - `client_cannot_provide_total_investment`
      - `client_contacts.name`
      - `client_relationship_manager.name`
      - `export_revenue`
      - `fdi_type.name`
      - `foreign_equity_investment`
      - `government_assistance`
      - `id`
      - `intermediate_company.name`
      - `investment_type.name`
      - `investor_company.name`
      - `likelihood_to_land.name`
      - `modified_on`
      - `new_tech_to_uk`
      - `non_fdi_r_and_d_budget`
      - `number_new_jobs`
      - `project_assurance_adviser.name`
      - `project_code`
      - `project_manager.name`
      - `r_and_d_budget`
      - `referral_source_activity.name`
      - `referral_source_activity_event`
      - `referral_source_activity_marketing.name`
      - `referral_source_activity_website.name`
      - `sector.name`
      - `site_decided`
      - `total_investment`
      - `uk_company.name`

  - An endpoint `POST /v4/dnb/company-create-investigation` was added for creating stub companies in DataHub for investigation by DNB.

  - The `POST /v4/dnb/company-create` endpoint was modified to return the boolean `pending_dnb_investigation` in responses representing created Data Hub companies.
    
    The format of the response is as follows:
    
        "pending_dnb_investigation": true,

  - Following endpoints were added to replace existing `/metadata` endpoint:
    
      - `GET /v4/metadata/administrative-area`
      - `GET /v4/metadata/business-type`
      - `GET /v4/metadata/capital-investment/asset-class-interest`
      - `GET /v4/metadata/capital-investment/construction-risk`
      - `GET /v4/metadata/capital-investment/deal-ticket-size`
      - `GET /v4/metadata/capital-investment/desired-deal-role`
      - `GET /v4/metadata/capital-investment/equity-percentage`
      - `GET /v4/metadata/capital-investment/investor-type`
      - `GET /v4/metadata/capital-investment/large-capital-investment-type`
      - `GET /v4/metadata/capital-investment/required-checks-conducted`
      - `GET /v4/metadata/capital-investment/restriction`
      - `GET /v4/metadata/capital-investment/return-rate`
      - `GET /v4/metadata/capital-investment/time-horizon`
      - `GET /v4/metadata/communication-channel`
      - `GET /v4/metadata/country`
      - `GET /v4/metadata/employee-range`
      - `GET /v4/metadata/event-type`
      - `GET /v4/metadata/evidence-tag`
      - `GET /v4/metadata/export-experience-category`
      - `GET /v4/metadata/fdi-type`
      - `GET /v4/metadata/fdi-value`
      - `GET /v4/metadata/headquarter-type`
      - `GET /v4/metadata/investment-activity-type`
      - `GET /v4/metadata/investment-business-activity`
      - `GET /v4/metadata/investment-delivery-partner`
      - `GET /v4/metadata/investment-investor-type`
      - `GET /v4/metadata/investment-involvement`
      - `GET /v4/metadata/investment-project-stage`
      - `GET /v4/metadata/investment-specific-programme`
      - `GET /v4/metadata/investment-strategic-driver`
      - `GET /v4/metadata/investment-type`
      - `GET /v4/metadata/likelihood-to-land`
      - `GET /v4/metadata/location-type`
      - `GET /v4/metadata/omis-market`
      - `GET /v4/metadata/order-cancellation-reason`
      - `GET /v4/metadata/order-service-type`
      - `GET /v4/metadata/overseas-region`
      - `GET /v4/metadata/policy-area`
      - `GET /v4/metadata/policy-issue-type`
      - `GET /v4/metadata/programme`
      - `GET /v4/metadata/project-manager-request-status`
      - `GET /v4/metadata/referral-source-activity`
      - `GET /v4/metadata/referral-source-marketing`
      - `GET /v4/metadata/referral-source-website`
      - `GET /v4/metadata/salary-range`
      - `GET /v4/metadata/sector`
      - `GET /v4/metadata/service-delivery-status`
      - `GET /v4/metadata/service`
      - `GET /v4/metadata/team-role`
      - `GET /v4/metadata/team`
      - `GET /v4/metadata/title`
      - `GET /v4/metadata/turnover`
      - `GET /v4/metadata/uk-region`
    
    The responses are exactly the same as their corresponding `/metadata` endpoints.
    
    New endpoints use Hawk authentication.

  - All `/metadata/*` endpoints are deprecated and will be removed on or after 15th October 2019. Please use corresponding `/v4/metadata` endpoints instead.

# Data Hub API 14.8.0 (2019-09-12)

## Removals

  - **Companies** `GET /v4/company/<id>>/timeline`: This deprecated endpoint was removed. Please use `/v4/activity-feed` instead.

## Deprecations

  - **Interactions** The field `location` is deprecated. Please check the API and Database schema categories for more details.

## Features

  - **OMIS** The notification logic in `datahub.omis` was adjusted to optionally use the `datahub.notification` app for triggering GOVUK notifications. This functionality can be switched on using a feature flag.

## Bug fixes

  - **Investment** The spellings of `Leisure` and `Commercial` in the Asset Class Interest metadata for Investor Profiles were fixed.

## API

  - **Advisers** The following endpoint was added:
    
      - `GET /v4/company-list/<id>`: Gets details of a single company list belonging to the authenticated user.
    
    Responses are in the following format:
    
        {
          "id": "string",
          "name": "string",
          "item_count": integer,
          "created_on": "ISO timestamp"
        }

  - **Companies** `GET /v4/company/<id>>/timeline`: This deprecated endpoint was removed. Please use `/v4/activity-feed` instead.

  - **Interactions** `GET,PATCH /v3/interaction/<uuid:pk>` and `GET,POST /v3/interaction`: the field `location` is deprecated and will be removed on or after 19 September.

  - **Interactions** The `/v3/search/interaction` endpoint was modified to return `company_one_list_group_tier` in search results. This will be in the following format:
    
        ...
        "company_one_list_group_tier": {
            "id": "b91bf800-8d53-e311-aef3-441ea13961e2",
            "name": "Tier A - Strategic Account"
        }
        ...
    
    The value could alternatively be null (if the interaction's company does not have a one list group tier).
    
    A filter was added to `/v3/search/interaction` - `company_one_list_group_tier` -which allows callers to filter interaction searches to companies attributed to a particular one list group tier.

  - A field `iso_alpha2_code` was added to the `GET /metadata/country/` API endpoint.
    
    This endpoint now returns results of the following format:
    
        ...
        {
            "id": "80756b9a-5d95-e211-a939-e4115bead28a",
            "name": "United Kingdom",
            "disabled_on": null,
            "overseas_region": null,
            "iso_alpha2_code": "GB"
        },
        {
            "id": "81756b9a-5d95-e211-a939-e4115bead28a",
            "name": "United States",
            "disabled_on": null,
            "overseas_region": {
                "name": "North America",
                "id": "fdfbbc8d-0e8a-479a-b10f-4979d582ff87"
            },
            "iso_alpha2_code": "US"
        },
        ...

## Database schema

  - **Companies** The `company__company` table now contains the `dnb_investigation_data` column.
    
    This column contains auxiliary data for the company that is required only for the purpose of investigation.

  - **Interactions** The column `interaction_interaction.location` is deprecated and will be removed on or after 19 September.

  - **Investment** `Bank` and `Corporate investor` were added to the `investor_type` metadata for `investor_profile`.

# Data Hub API 14.7.0 (2019-09-05)

## Deprecations and removals

  - **Interactions** The `metadata_service.name` column was removed from the database.

## Internal changes

  - The `sync_es` management command was updated to use Celery.
    
    By default, the Celery task runs asynchronously. `--foreground` can be passed to run the Celery task synchronously (without Celery running).
    
    The `--batch_size` argument was removed as it is rarely used and isn't currently supported by the Celery task.

## API

  - **Advisers** The following endpoint was added:
    
    `PUT /v4/company-list/<company list ID>/item/<company ID>`
    
    This adds a company to the user's own selected list of companies.
    
    If the operation is successful, a 204 status code will be returned. If there is no company list with specified company list ID or company with the specified company ID, a 404 will be returned.
    
    If an archived company is specified, a 400 status code will be returned and response body will contain:
    
        {
            "non_field_errors": "An archived company can't be added to a company list."
        }
    
    Otherwise, the response body will be empty.

  - **Advisers** `GET /v4/company-list`, `PATCH /v4/company-list/<id>`: An `item_count` field was added to response items containing the count of items in the list.

  - **Advisers** The following endpoint was added:
    
    `GET /v4/company-list/<company list ID>/item`
    
    It lists all the companies on the authenticated user's selected list, with responses in the following format:
    
        {
            "count": <int>,
            "previous": <url>,
            "next": <url>,
            "results": [
                {
                    "company": {
                        "id": <string>,
                        "archived": <boolean>,
                        "name": <string>,
                        "trading_names": [<string>, <string>, ...]
                    },
                    "created_on": <ISO timestamp>,
                    "latest_interaction": {
                        "id": <string>,
                        "created_on": <ISO timestamp>,
                        "date": <ISO date>,
                        "subject": <string>
                    }
                },
                ...
            ]
        }
    
    `latest_interaction` may be `null` if the company has no interactions.
    
    Results are sorted by `latest_interaction.date` in reverse chronological order, with `null` values last.
    
    The endpoint has pagination in line with other endpoints; to retrieve all results pass a large value for the `limit` query parameter (e.g. `?limit=1000`).
    
    If selected list does not exist, the endpoint will return 404 status code.

  - **Advisers** The following endpoint was added:
    
    `DELETE /v4/company-list/<company list ID>/item/<company ID>`
    
    This removes a company from the user's own selected list of companies.
    
    If the operation is successful, a 204 status code will be returned. If there is no company list with specified company list ID or a list doesn't belong to the user, a 404 will be returned.

  - **OMIS** The following endpoint was added:
    
      - `GET /v4/dataset/omis-dataset`: Present required fields data of all orders to be consumed by data-flow and used in data-workspace for reporting and analyst access.

## Database schema

  - **Interactions** The `metadata_service.name` column was removed from the database.

# Data Hub API 14.6.0 (2019-09-03)

## Deprecations and removals

  - **Companies** `GET /v4/company/<id>>/timeline`: This endpoint is deprecated and will be removed on or after 9 September 2019. Please use `/v4/activity-feed` instead.
  - **Contacts** `POST /v3/search/contact`, `POST /v3/search/contact/export` the following `sortby` values are deprecated and will be removed on or after 12 September 2019:
      - `accepts_dit_email_marketing`
      - `address_county`
      - `address_same_as_company`
      - `address_town`
      - `adviser.name`
      - `archived`
      - `archived_by.name`
      - `archived_on`
      - `company_sector.name`
      - `email`
      - `first_name`
      - `id`
      - `job_title`
      - `name`
      - `primary`
      - `telephone_countrycode`
      - `telephone_number`
      - `title.name`
  - **Investment** `POST /v3/search/investment_project`, `POST /v3/search/investment_project/export` the following `sortby` values are deprecated and will be removed on or after 12 September 2019:
      - `actual_land_date`
      - `approved_commitment_to_invest`
      - `approved_fdi`
      - `approved_good_value`
      - `approved_high_value`
      - `approved_landed`
      - `approved_non_fdi`
      - `archived`
      - `archived_by.name`
      - `average_salary.name`
      - `business_activities.name`
      - `client_cannot_provide_total_investment`
      - `client_contacts.name`
      - `client_relationship_manager.name`
      - `export_revenue`
      - `fdi_type.name`
      - `foreign_equity_investment`
      - `government_assistance`
      - `id`
      - `intermediate_company.name`
      - `investment_type.name`
      - `investor_company.name`
      - `likelihood_to_land.name`
      - `modified_on`
      - `new_tech_to_uk`
      - `non_fdi_r_and_d_budget`
      - `number_new_jobs`
      - `project_assurance_adviser.name`
      - `project_code`
      - `project_manager.name`
      - `r_and_d_budget`
      - `referral_source_activity.name`
      - `referral_source_activity_event`
      - `referral_source_activity_marketing.name`
      - `referral_source_activity_website.name`
      - `sector.name`
      - `site_decided`
      - `total_investment`
      - `uk_company.name`

## API

  - **Advisers** The following endpoint was added:
      - `DELETE /v4/company-list/<list ID>`: Delete a company list and all its items.
  - **Advisers** `GET /v4/company-list`: The `items__company_id` query parameter can now be used to get the authenticated user's lists that contain a particular company.
  - **Advisers** The following endpoint was added:
      - `PATCH /v4/company-list/<list ID>`: Rename a company list.
        
        The request body must be in following format:
        
            {
              "name": "string"
            }

## Database schema

  - **Companies** The `pending_dnb_investigation` field in the `company_company` table is now non-nullable.

# Data Hub API 14.5.0 (2019-08-29)

## Internal changes

  - **Advisers** An internal constraint preventing multiple company lists per user was removed now that the existing company list functionality is aware of multiple lists.

## API

  - **Advisers** The following endpoint was added:
      - `POST /v4/company-list`: Create a company list for the authenticated user.
        
        The request body must be in following format:
        
            {
              "name": "string"
            }
  - **Advisers** The following endpoint was added:
      - `GET /v4/company-list`: Lists the authenticated user's company lists.
        
        This is a paginated endpoint. Items are sorted by name, and are in the following format:
        
            {
              "id": "string",
              "name": "string",
              "created_on": "ISO timestamp"
            }

## Database schema

  - **Companies** The `company_company` table now has a boolean field called `pending_dnb_investigation`. This is to record whether a company is under DNB investigation.

# Data Hub API 14.4.0 (2019-08-23)

## Deprecations and removals

  - **Advisers** The `company_list_companylisttem.adviser_id` column is deprecated and will be removed on or after 2 September 2019.

## Features

  - The `datahub.notification` app was adapted so that it can work with multiple GOVUK notify API keys - so that different apps can define their GOVUK notify templates on different notify service instances.

## Bug fixes

  - **Interactions** Meeting invite ingestion was adjusted so that users do not get error notifications when they send a meeting cancellation.
    
    The notification celery task was modified so that 400/403 level responses do not have automatic retries.

## Internal changes

  - **Advisers** The initial teams fixture (used for tests and new environments) was updated so that only the `DIT_staff` group has permission to use the company lists feature.
  - **Advisers** All legacy company list endpoints now fully operate on a default list for each user. This is in preparation for it being possible for users to have multiple company lists.

## Database schema

  - **Advisers** The `company_list_companylisttem.adviser_id` column was made nullable.

# Data Hub API 14.3.0 (2019-08-22)

## Internal changes

  - **Advisers** A data migration was added to associate all existing company list items with a default list for each user. This is in preparation for it being possible for users to have multiple company lists.
  - Celery was [configured to send task events by default](http://docs.celeryproject.org/en/latest/userguide/configuration.html#events) (for better compatibility with the Flower monitoring tool).
  - The Celery `conf` inspect command was disabled for security reasons.

## API

  - An endpoint was added for creating companies through dnb-service (<https://github.com/uktrade/dnb-service/>) given a `duns_number`.

## Database schema

  - **Advisers** `company_list_companylisttem.list_id` was made `NOT NULL`.

# Data Hub API 14.2.0 (2019-08-19)

## Deprecations and removals

  - **Investment** `POST /v3/search/investment_project`: The `sortby` value `referral_source_adviser.name` is no longer accepted.
    
    This `sortby` value was non-functional and was returning a 500 error if an attempt to use it was made.

## Features

  - **Interactions** It is now possible to upload interactions with service answers using the interaction upload tool in the Django admin.

## Internal changes

  - **Advisers** Items added to company lists are now internally associated with a default list for each user. This is in preparation for it being possible for users to have multiple company lists.
  - All remaining uses of the `copy_to` mapping parameter were removed from all Elasticsearch mapping types. All search queries were updated to use corresponding sub-fields instead.

## Database schema

  - **Advisers** A `company_list_companylist` table with the following columns was created:
    
      - `"created_on" timestamp with time zone NULL`
      - `"modified_on" timestamp with time zone NULL`
      - `"id" uuid NOT NULL PRIMARY KEY`
      - `"name" varchar(255) NOT NULL`
      - `"is_legacy_default" boolean NOT NULL`
      - `"adviser_id" uuid NOT NULL`
      - `"created_by_id" uuid NULL`
      - `"modified_by_id" uuid NULL`
    
    This will be used to store the IDs and names of user-created lists of companies.

  - **Advisers** A `"list_id" uuid NULL` column was added to the `company_list_companylisttem` table.

# Data Hub API 14.1.0 (2019-08-15)

## Deprecations and removals

  - **Interactions** `interaction_interaction`: The deprecated `dit_adviser_id` and `dit_team_id` columns were removed. Please use the `interaction_interactionditparticipant` table instead.

  - The following management commands were removed as they are no longer required:
    
      - `update_investment_project_archived_state`
      - `update_investment_project_comments`
      - `update_investment_project_delivery_partners`
      - `update_investment_project_referral_source_activity_marketing`
      - `update_investment_project_referral_source_activity_website`
      - `update_omis_uk_regions`
      - `update_service_delivery_grant_fields`
    
    These commands were used to make corrections following the initial data migration into Data Hub and no longer in use.

## Internal changes

  - Various sub-fields were added to all Elasticsearch mapping types as replacements for the few remaining uses of the `copy_to` mapping parameter.

# Data Hub API 14.0.0 (2019-08-12)

## Deprecations and removals

  - **Interactions** `GET /v3/interaction, GET /v3/interaction/<id>, POST /v3/interaction, PATCH /v3/interaction/<id>`: The deprecated `dit_adviser` and `dit_team` fields were removed from responses. Please use `dit_participants` instead.
  - **Interactions** `interaction_interaction`: The deprecated `dit_adviser_id` and `dit_team_id` columns were prepared for removal and will shortly be removed. Please use the `interaction_interactionditparticipant` table instead.

## Features

  - **Contacts** The search CSV export was updated to handle interactions with multiple teams in the 'Team of latest interaction' column. Multiple team names are separated by commas, and duplicate teams are omitted. The column was accordingly renamed 'Teams of latest interaction'.
  - **Interactions** It's now possible to edit the advisers and teams associated with an interaction from the admin site.
  - It's now possible to configure Gunicorn to [emit monitoring metrics](http://docs.gunicorn.org/en/stable/instrumentation.html) to a StatsD host.

## Bug fixes

  - **Interactions** An out-of-memory crash when trying to import a CSV file with blank `contact_email` values was fixed.
    
    (This would only have happened if there were a large number of active contacts in the database with blank email addresses.)

## API

  - **Companies** `POST /v4/dnb/company-search`: This endpoint was modified to ensure that DNB results were hydrated with the corresponding Data Hub company, if it is present and can be matched (by duns number).
    
    The API response returns Data Hub companies alongside DNB data in the following format:
    
        "datahub_company": {
            "id": "0f5216e0-849f-11e6-ae22-56b6b6499611",
            "latest_interaction": {
                "id": "e8c3534f-4f60-4c93-9880-09c22e4fc011",
                "created_on": "2018-04-08T14:00:00Z",
                "date": "2018-06-06",
                "subject": "Exported to Canada"
            }
        }

# Data Hub API 13.14.0 (2019-08-06)

## Features

  - **Interactions** The `service` metadata data model has been changed from a flat list of services to a tree structure with a help of `django-mptt` library.

  - **Interactions** It is now possible to monitor the number of failed and successful calendar invites being ingested in DataHub using StatsD.

  - The API documentation at the URL path `/docs` was updated to use OpenAPI following the upgrade to Django Rest Framework 3.10.0.
    
    It is now enabled by default.
    
    There are currently some missing or incorrect details as we are dependent on the web framework we are using. These should be corrected over time.

## Bug fixes

  - Comma- and semicolon-delimited values in CSV exports are now always sorted alphabetically. (Previously, they were in an unspecified order which could change between exports.)

## Database schema

  - **Interactions** The `metadata_service` table column `name` is deprecated and will be removed on or after the 5th of September 2019.

  -   - **Interactions** The following columns were added to `metadata_service` table to transform flat services list into a tree structure:
        
          - segment (character varying(255)) not null
          - level (integer) not null
          - lft (integer) not null
          - parent\_id (uuid)
          - rght (integer) not null
          - tree\_id (integer) not null
    
    Columns `level`, `lft`, `rght`, `tree_id` are being used by `django-mptt` library to manage the tree structure.
    
    The `parent_id` field points at the parent service.
    
    At present only the leaf nodes are being used as interaction's service foreign keys.

# Data Hub API 13.13.2 (2019-08-05)

## Bug fixes

  - **Advisers** `PUT /v4/user/company-list/<company ID>`: A bug was fixed where multiple companies could not be added to a company list.

## Internal changes

  - The Gunicorn log format was updated to include request times in seconds.

# Data Hub API 13.13.1 (2019-07-31)

## Internal changes

  - **Interactions** A migration was updated to not create a database index concurrently due to a problem encountered during deployment.

# Data Hub API 13.13.0 (2019-07-30)

## API

  - **Advisers** The following endpoint was added:
    
    `GET /v4/user/company-list`
    
    It lists all the companies on the authenticated user's personal list, with responses in the following format:
    
        {
            "count": <int>,
            "previous": <url>,
            "next": <url>,
            "results": [
                {
                    "company": {
                        "id": <string>,
                        "archived": <boolean>,
                        "name": <string>,
                        "trading_names": [<string>, <string>, ...]
                    },
                    "created_on": <ISO timestamp>,
                    "latest_interaction": {
                        "id": <string>,
                        "created_on": <ISO timestamp>,
                        "date": <ISO date>,
                        "subject": <string>
                    }
                },
                ...
            ]
        }
    
    `latest_interaction` may be `null` if the company has no interactions.
    
    Results are sorted by `latest_interaction.date` in reverse chronological order, with `null` values last.
    
    The endpoint has pagination in line with other endpoints; to retrieve all results pass a large value for the `limit` query parameter (e.g. `?limit=1000`).

# Data Hub API 13.12.0 (2019-07-25)

## Deprecations and removals

  - **Interactions** The `metadata_service.requires_service_answers_flow_feature_flag` column was removed from the database.

## Features

  - **Companies** The admin site company merging tool now updates users' personal company lists if they contain the company being archived.

## API

  - **Advisers** `PUT /v4/user/company-list/<company ID>`: A 400 is now returned if an archived company is specified.
    
    In this case, the response body will contain:
    
        {
            "non_field_errors": "An archived company can't be added to a company list."
        }
    
    (Note that it is still possible to remove archived companies from a user's company list.)

  - **Advisers** The following endpoint was added:
    
      - `GET /v4/user/company-list/<company ID>`
    
    It checks if a company is on the authenticated user's personal list of companies.
    
    If the company is on the user's list, a 2xx status code will be returned. If it is not, a 404 will be returned.

  - **Advisers** The following endpoint was added:
    
    `DELETE /v4/user/company-list/<company ID>`
    
    This removes a company from the authenticated user's personal list of companies.
    
    If the operation is successful, a 2xx status code will be returned. If there is no company with the specified company ID, a 404 will be returned.
    
    Currently, the response body is unused.

## Database schema

  - **Interactions** The `metadata_service.requires_service_answers_flow_feature_flag` column was removed from the database.

# Data Hub API 13.11.0 (2019-07-22)

## Deprecations and removals

  - **Interactions** The `metadata_service.requires_service_answers_flow_feature_flag` column is deprecated will be removed on or after 22 July 2019.

## Features

  - **Interactions** The ability to send received and bounce notifications in case of success and failure of ingesting calendar invite emails respectively has been added to the DataHub.
    
    This is currently behind the `interaction-email-notification` feature flag.

  - **Interactions** The `interaction_service_answers_flow` feature flag was removed and the related functionality is no longer behind a feature flag.

  - An initial endpoint was added for searching for companies through dnb-service (<https://github.com/uktrade/dnb-service/>). This endpoint takes care of auth and proxies requests through to the service - it will return error responses from the proxied DNB service.
    
    There is further work to be done here in terms of iterating features and hardening the implementation.

## Bug fixes

  - **Investment** The schema in the API documentation was corrected for all investment document upload callback endpoints.

## Internal changes

  - Django Rest Framework was updated from version 3.9.4 to version 3.10.1.

# Data Hub API 13.10.0 (2019-07-17)

## Internal changes

  - **Interactions** The context of "Export Opportunities" service has been updated to include export interaction.

## API

  - **Advisers** The following endpoint was added:
    
    `PUT /v4/user/company-list/<company ID>`
    
    This adds a company to the authenticated user's personal list of companies.
    
    If the operation is successful, a 2xx status code will be returned. If there is no company with the specified company ID, a 404 wil lbe returned.
    
    Currently, the response body is unused.

## Database schema

  - **Advisers** A `company_list_companylistitem` table was created with the following columns:
    
      - `"id" uuid NOT NULL PRIMARY KEY`
      - `"adviser_id" uuid NOT NULL`
      - `"company_id" uuid NOT NULL`
      - `"created_on" timestamp with time zone NULL`
      - `"modified_on" timestamp with time zone NULL`
      - `"created_by_id" uuid NULL`
      - `"modified_by_id" uuid NULL`
    
    This table will store a list of companies advisers have added to their personal list of companies.

# Data Hub API 13.9.0 (2019-07-16)

## Features

  - **Interactions** The service names were changed to enable front-end to display them in hierarchy. Services no longer required have been disabled.

## Bug fixes

  - Schemas in the API documentation were corrected for the following endpoints:
      - all archive endpoints
      - all unarchive endpoints
      - the complete OMIS order endpoint
      - the cancel OMIS order endpoint
      - all search endpoints

## Internal changes

  - Python was updated from version 3.7.3 to 3.7.4 in deployed environments.

## API

  - **Interactions** `POST /v3/interaction` now accepts TAP related fields `grant_amount_offered` and `net_company_receipt` for interaction.

  - **Investment** The following endpoints were corrected to return a 404 when a non-existent investment project or proposition was specified:
    
      - `GET,POST /v3/investment/{project_pk}/proposition/{proposition_pk}/document`
      - `GET,DELETE /v3/investment/{project_pk}/proposition/{proposition_pk}/document/{entity_document_pk}`
      - `GET /v3/investment/{project_pk}/proposition/{proposition_pk}/document/{entity_document_pk}/download`
      - `POST /v3/investment/{project_pk}/proposition/{proposition_pk}/document/{entity_document_pk}/upload-callback`
    
    (Previously, they would only return a 404 in some of the possible cases.)

## Database schema

  - An `order double precision` column was added to the `metadata_service` table to store the order of services.

# Data Hub API 13.8.0 (2019-07-10)

## Features

  - The Django Rest Framework built-in documentation was enabled at the URL path `/docs`.
    
    This is currently only enabled if the `ENABLE_API_DOCUMENTATION` environment variable is set to `True` as the documentation is not fully functional as yet.
    
    You must also log into Django admin prior to accessing `/docs`.

  - A new `notification` django app was added for the purpose of sending notifications to Data Hub advisers and contacts. This is a wrapper around the GOVUK Notify service and will be used initially for sending receipt/bounce notifications to advisers who use the meeting invite email ingestion tool.
    
    The app has not yet been added to `settings.INSTALLED_APPS`; this will happen as part of the follow-up work to use the notification app in the meeting invite email ingestion logic.

## Bug fixes

  - An upgrade to sentry-sdk was reverted due to an [observed memory leak](https://github.com/getsentry/sentry-python/issues/419).

# Data Hub API 13.7.0 (2019-07-09)

## Internal changes

  - **Interactions** The meeting email invites ingestion parsing logic was adjusted to use a new `max_interactions` strategy for finding a contact. This ensures that when multiple contacts are found which match the same email address, the contact with the most interactions attributed to it takes precedence. It's an imperfect solution, but acts as a best guess for imperfect data.

## API

  - The activity-stream payload for OMIS and investment projects will now contain `startTime`.

# Data Hub API 13.6.1 (2019-07-08)

## Internal changes

  - The `/whoami/` endpoint was opted out of atomic requests as it does not require them. This change is intended to help reduce the occurence of a race condition that occurs when two requests perform OAuth2 introspection on the same token.

# Data Hub API 13.6.0 (2019-07-02)

## API

  - **Interactions** `GET /v3/interaction`, `GET /v3/interaction/<id>`: A `service_answers` field was added to responses.

  - **Interactions** `POST /v3/interaction`, `PATCH /v3/interaction/<id>`: An optional (depending on selected Service) `service_answers` field was added to request bodies.
    
    The `service_answers` body is expected to be in the following format:
    
        {
            "<service question ID>": {
                "<service answer option ID>": {
                    # body reserved for future use
                }
            },
            ...
        }

  - The activity-stream payload will now contain `dit:team` for all `dit:DataHubAdviser`.

## Database schema

  - **Interactions** A nullable `service_answers jsonb` column was added to the `interaction_interaction` table to store answers to service questions.

# Data Hub API 13.5.0 (2019-06-18)

## Features

  - **Interactions** The Django Admin Interaction Service section has been made read only.

## Internal changes

  - **Events** Events in the test data for acceptance tests were corrected to use a DIT service that is valid for events.

## API

  - **Interactions** `GET /metadata/service/`: The `interaction_questions` field was added to responses. It contains a representation of service questions and answer options from `ServiceQuestion` and `ServiceAnswerOption` models. It is an array of following format:
    
        [ # Array of ServiceQuestion
            {
                'id': <uuid>,
                'name: <str>,
                'disabled_on': <datetime>,
                'answer_options': [ # Array of ServiceAnswerOption
                    {
                        'id': <uuid>,
                        'name': <str>,
                        'disabled_on': <datetime>
                    },
                    ...
                ]
            },
            ...
        ]

  - The activity-stream payload will now contain `dit:jobTitle` for all `dit:DataHubContact`.

  - The activity-stream payload will now contain `url` for all `dit:DataHubContact`.

# Data Hub API 13.4.0 (2019-06-14)

## Features

  - **Interactions** The services in production were replicated to all other environments in preparation for forthcoming changes to interactions and services.

## Bug fixes

  - **OMIS** When a company or a contact name changes, related OMIS orders are now synced to ElasticSearch.

## Internal changes

  - **Interactions** A feature flag with code `interaction_service_answers_flow` was added to control whether services with service questions and answer options are returned by the API.
  - The deprecated Raven Sentry client was replaced with the Sentry SDK.

## Database schema

  - **Interactions** A `metadata_service.requires_service_answers_flow_feature_flag` column was added with type `boolean`. This is used to hide certain services behind a feature flag while related functionality is being built.

# Data Hub API 13.3.0 (2019-06-11)

## Features

  - **Interactions** The admin site import interactions tool is no longer behind a feature flag.

## API

  - **Interactions** `POST /v3/interaction, PATCH /v3/interaction/<id>`: The API now correctly returns an error if `service_delivery` is specified for `kind` when `theme` is `investment`.

  - It is now possible to get a list of OMIS orders added in activity-stream [format.](https://www.w3.org/TR/activitystreams-core/)
    
    The URL for this is:
    
    /v3/activity-stream/omis/order-added

# Data Hub API 13.2.0 (2019-06-06)

## Deprecations and removals

  - **Interactions** `POST /v3/interaction, PATCH /v3/interaction/<id>`: The deprecated `dit_adviser` and `dit_team` fields were made read-only in preparation for their removal. Please use `dit_participants` instead.
  - **Interactions** `POST /v3/search/interaction`: The deprecated `dit_adviser` filter was removed. Please use the `dit_participants__adviser` filter instead.
  - **Interactions** `POST /v3/search/interaction`: The deprecated `dit_adviser_name` filter was removed. There is no replacement for this filter.
  - **Interactions** `GET /v3/search`, `POST /v3/search/interaction`: The deprecated `dit_adviser` and `dit_team` interaction fields were removed from interaction objects in responses. Please use `dit_participants` instead.
  - **Interactions** `POST /v3/search/interaction`: The deprecated `dit_team` filter was removed. Please use the `dit_participants__team` filter instead.

## Features

  - **Interactions** The theme field was added to the import interactions admin site tool. The tool is currently behind the `admin-interaction-csv-importer` feature flag as it’s incomplete.

  - **Interactions** A feature was activated for ingesting meeting invite emails sent to a shared mailbox as draft interactions. This enables DIT advisers to create interactions more easily.
    
    This is the first instance of a Data Hub app using the framework provided by the `datahub.email_ingestion` app. There will be subsequent iterations on the `CalendarInteractionEmailProcessor` class to improve the user experience - most notably sending notifications of bounce/receipt to advisers.

## API

  - `GET /v4/activity-feed` now returns an empty list if the authenticated user doesn't have permissions to view all interactions, investment projects or OMIS orders.

  - It is now possible to get a list of investment projects created in activity-stream [format.](https://www.w3.org/TR/activitystreams-core/)
    
    The URL for this is:
    
    /v3/activity-stream/investment/project-added

# Data Hub API 13.1.0 (2019-06-03)

## Features

  - **Interactions** The ability to download records that could not be matched to contacts was added to the import interactions admin site tool. The tool is currently behind the `admin-interaction-csv-importer` feature flag as it’s incomplete.

  - **Interactions** The import interactions admin site tool now rejects files that contain duplicate items. The tool is currently behind the `admin-interaction-csv-importer` feature flag as it’s incomplete.

  - **Interactions** The search CSV export was updated to handle interactions with multiple advisers. The previous Adviser and Service provider columns have been merged into a single Advisers column. This column contains the names of all the advisers for each interaction separated by commas. The team of each adviser is in brackets after each name.
    
    For existing interactions, existing teams associated with each interaction have been preserved. For new interactions, the team included is the team each adviser was in when they were added to the interaction.

## Database schema

  - **Interactions** A GIN index for `source` was added to the `interaction_interaction` table.

# Data Hub API 13.0.0 (2019-05-29)

## Features

  - **Interactions** The ability to save loaded interactions was added to the import interactions admin site tool. The tool is currently behind the `admin-interaction-csv-importer` feature flag as it’s incomplete.

## Bug fixes

  - **Investment** A fix was applied to the SPI report generation task so that it restarts if it's interrupted.

## API

  - New endpoint added `GET /v4/activity-feed` which acts as a proxy for Activity Stream and allows a Data Hub frontend client to read from it.

  - It is now possible to get a list of interactions in activity-stream [format.](https://www.w3.org/TR/activitystreams-core/)
    
    The URL for this is:
    
    `/v3/activity-stream/interactions`

## Database schema

  - **Interactions** The database table `interaction_serviceadditionalquestion` has been added with the following columns:
      - `id uuid not null`
      - `disabled_on timestamp with time zone`
      - `name text not null`
      - `is_required boolean not null`
      - `type character varying(255) not null`
      - `order double precision not null`
      - `answer_option_id uuid not null`
  - **Interactions** The database table `interaction_serviceansweroption` has been added with the following columns:
      - `id uuid not null`
      - `disabled_on timestamp with time zone`
      - `name text not null`
      - `order double precision not null`
      - `question_id uuid not null`
  - **Interactions** The database table `interaction_servicequestion` has been added with the following columns:
      - `id uuid not null`
      - `disabled_on timestamp with time zone`
      - `name text not null`
      - `order double precision not null`
      - `service_id uuid not null`

# Data Hub API 12.3.0 (2019-05-22)

## API

  - **Companies** `PATCH /v4/company/<uuid:pk>`: `headquarter_type` and `global_headquarters` can now always be changed. They were previously read-only if a company had a non-empty `duns_number` set.

# Data Hub API 12.2.0 (2019-05-17)

## Deprecations and removals

  - **Companies** The trading\_address fields have now been removed from the `company_company` table in the database. These include:
    
    trading\_address\_1  
    trading\_address\_2  
    trading\_address\_town  
    trading\_address\_county  
    trading\_address\_country  
    trading\_address\_postcode

  - **Companies** The `/v3/ch-company/*` endpoints have been removed. These include:
    
    /v3/ch-company  
    /v3/ch-company/\<company-number\>

## API

  - **Investment** The validation for the endpoint `PATCH /v4/investor-profile/` has been updated.
    
    The field `required_checks_conducted_on` now needs to be a date that is within the last 12 months.

## Database schema

  - **Investment** The database table used to store large capital investor profiles has been changed from `investor_profile_investorprofile` to `investor_profile_largecapitalinvestorprofile`.
    
    The column `profile_type_id` was removed.
    
    The database tables `investor_profile_investorprofile` and `investor_profile_profiletype` will be removed on or before 27th May.

# Data Hub API 12.1.0 (2019-05-13)

## Deprecations and removals

  - **Companies** The trading\_address fields have now been removed from the codebase. These include:
    
    trading\_address\_1  
    trading\_address\_2  
    trading\_address\_town  
    trading\_address\_county  
    trading\_address\_country  
    trading\_address\_postcode

## Features

  - **Interactions** A preview page was added to the admin site tool for importing interactions. The tool is currently behind the `admin-interaction-csv-importer` feature flag as it is incomplete.

# Data Hub API 12.0.0 (2019-05-09)

## Deprecations and removals

  - **Companies** On 16 May 2019, the `company_company.trading_address_<xyz>` columns will be removed from the database. These include:
    
    `trading_address_1`  
    `trading_address_2`  
    `trading_address_town`  
    `trading_address_county`  
    `trading_address_country_id`  
    `trading_address_postcode`

  - **Companies** The `/v3/company` endpoints have been removed. These include:
    
    `/v3/company`  
    `/v3/company/<uuid:pk>`  
    `/v3/company/<uuid:pk>/archive`  
    `/v3/company/<uuid:pk>/audit`  
    `/v3/company/<uuid:pk>/one-list-group-core-team`  
    `/v3/company/<uuid:pk>/timeline`  
    `/v3/company/<uuid:pk>/unarchive`

  - The `/v3/search/company/` endpoints have been removed. These include:
    
    `/v3/search/company`  
    `/v3/search/company/autocomplete`  
    `/v3/search/company/export`

## Features

  - **Interactions** Validation of rows in the input file was added to the admin site tool for importing interactions. The tool is currently behind the `admin-interaction-csv-importer` feature flag as it is incomplete.

## Internal changes

  - **Investment** The logic to streamline the investment flow by removing the assign pm stage has been removed. The logic was hidden behind a feature flag that was never activated.

## API

  - **Companies** The endpoint `/v4/search/company/autocomplete` has been updated to accept an optional parameter of `country`.
    
    Company typeahead searches are now filterable by `country` the filter accepts a single or list of country ids.

## Database schema

  - **Interactions** The `interaction_interaction` table has been modified such that the following columns are no longer nullable:
      - `status` - this has an application-enforced default of 'complete'
      - `location` - this has an application-enforced default of ''
      - `archived` - this has an application-enforced default of false

# Data Hub API 11.12.0 (2019-05-02)

## Internal changes

  - The `update_company_registered_address` Django command is now available for internal use. This copies the `registered_address` of all CompaniesHouseCompany records to the corresponding Company record with the same `company_number`. If a CompaniesHouseCompany is not found, it resets the `registered_address`.

## API

  - **Companies** New API endpoints were added to aid matching Data Hub companies with D\&B companies:
    
    All endpoints return a response body with the following format:
    
        {
            "result": {
                ...
            },
            "candidates": [
                { ... },
                { ... }
            ],
            "company": {
                "id": "81756b9a-5d95-e211-a939-e4115bead28a",
                "name": 'My Corp',
                "trading_names": ["trading name"]
            }
        }
    
    The value of `result` depends on the type of match.
    
    If a match was found and recorded:
    
        {
            "dnb_match": {
                "duns_number": "111",
                'name': 'NAME OF A COMPANY',
                "country": {
                    "id": "81756b9a-5d95-e211-a939-e4115bead28a",
                    "name": "United States"
                },
                "global_ultimate_duns_number": "112",
                "global_ultimate_name": "NAME OF A GLOBAL COMPANY",
                "global_ultimate_country": {
                    "id": "81756b9a-5d95-e211-a939-e4115bead28a",
                    "name": "United States"
                },
            },
            "matched_by": "data-science"
        },
    
    If `matched_by` contains `adviser` value, then additional `adviser` key will be added to the `result` response:
    
        {
            ...
            "matched_by": "adviser",
            "adviser": {
                "id": "12777b9a-5d95-2241-a939-fa112be2d22a",
                "first_name": "John",
                "last_name": "Doe",
                "name": "John Doe"
            }
        },
    
    If a match wasn't found because the company isn't listed or the adviser is not confident to make the match:
    
        {
            "no_match": {
                "reason': "not_listed",  # or "not_confident"
            },
            "matched_by": "adviser",
            "adviser": { ... }
        },
    
    If a match wasn't found because there were multiple potential matches:
    
        {
            "no_match": {
                "reason": "more_than_one",
                "candidates": [  # list of duns numbers
                    "123456789",
                    "987654321"
                ]
            },
            "matched_by": "adviser",
            "adviser": { ... }
        },
    
    If a match wasn't found because of other reasons:
    
        {
            "no_match": {
                "reason": "other",
                "description": "explanation..."
            },
            "matched_by": "adviser",
            "adviser": { ... }
        },
    
    The top level `candidates` is a list of objects with this format:
    
        {
            "duns_number": 12345,
            "name": 'test name',
            "global_ultimate_duns_number": 12345,
            "global_ultimate_name": "test name global",
            "global_ultimate_country": {
                "id": "81756b9a-5d95-e211-a939-e4115bead28a",
                "name": "United States"
            },
            "address_1": "1st LTD street",
            "address_2": "",
            "address_town": "London",
            "address_postcode": "SW1A 1AA",
            "address_country": {
                "id": "81756b9a-5d95-e211-a939-e4115bead28a",
                "name": "United States"
            },
            "confidence": 10,
            "source": "cats"
        }
    
    Endpoints:
    
    `GET /v4/dnb-match/<company_pk>` returns the response above
    
    `POST /v4/dnb-match/<company_pk>/select-match` accepts the `duns_number` of the candidate to be selected as a match from the list of candidates
    
    `POST /v4/dnb-match/<company_pk>/select-no-match` accepts `reason` with value:
    
      - `not_listed`: if none of the candidates is a good match
      - `not_confident`: if the adviser is not confident to make the match
      - `more_than_one`: if there are multiple potential matches. In this case an extra `candidates` field is required with the list of valid duns numbers.
      - `other`: for other reasons. In this case an extra free text `description` field is required

  - **Investment** The field `actual_land_date` is now required to move an investment project from active to verify win.

# Data Hub API 11.11.0 (2019-04-30)

## Deprecations and removals

  - **Companies** On the 4th of May 2019, all data in the `company_company` registered address fields will be replaced by the official data from the Companies House record identified by the `company_company.company_number` field. In cases where `company_company.company_number` is invalid or blank (e.g. for non-UK companies), the registered address fields will be made blank and the related data lost. List of registered address fields:
      - `registered_address_1`
      - `registered_address_2`
      - `registered_address_town`
      - `registered_address_county`
      - `registered_address_postcode`
      - `registered_address_country_id`

## Internal changes

  - **Companies** The field `company.Company.registered_address_country` was made blankable so that it becomes optional in the Django admin.
  - The `company_field_with_copy_to_name_trigram` search field type was removed and uses of it replaced with `company_field`. The `name.keyword`, `name.trigram` and `trading_names.trigram` sub-fields are now used in search queries. This change also means that the type of the `name` sub-field has been corrected from `keyword` to `text`.
  - Python was updated from version 3.7.2 to 3.7.3 in deployed environments.

## Database schema

  - **Companies** The following columns were made `NOT NULL` - optional values will be represented by empty strings:
      - `company_company.registered_address_2`
      - `company_company.registered_address_county`
      - `company_company.registered_address_postcode`
      - `company_company.address_1`
      - `company_company.address_2`
      - `company_company.address_town`
      - `company_company.address_county`
      - `company_company.address_postcode`
      - `company_company.trading_address_1`
      - `company_company.trading_address_2`
      - `company_company.trading_address_town`
      - `company_company.trading_address_county`
      - `company_company.trading_address_postcode`

# Data Hub API 11.10.0 (2019-04-25)

## Deprecations and removals

  - **Interactions** The deprecated `interaction_interaction.contact_id` column was deleted from the database. Please use the `interaction_interaction_contacts` many-to-many table instead.

## Internal changes

  - **Investment** The logic has been updated for selecting which financial year's data is used to calculate the GVA for an investment project.
  - The `name.keyword` and `name.trigram` sub-fields of the `contact_or_adviser_field` field type are now used in search queries. Hence, the `name_trigram` sub-field of `contact_or_adviser_field` has been removed, and the type of the `name` sub-field has been changed from `keyword` to `text`.

## API

  - **Interactions** `GET /v3/interaction`, `GET /v3/interaction/<id>`: A `theme` field was added to responses with possible values `"export"`, `"investment"`, `"other"` and `null`.
  - **Interactions** `POST /v3/interaction`, `PATCH /v3/interaction/<id>`: An optional `theme` field was added to request bodies with possible values `"export"`, `"investment"`, `"other"` and `null`.
  - **Investment** The endpoint `/v4/large-investor-profile` has been updated to allow the following fields to be set to empty values.
      - investor\_type
      - minimum\_return\_rate
      - minimum\_equity\_percentage

## Database schema

  - **Interactions** The deprecated `interaction_interaction.contact_id` column was deleted from the database. Please use the `interaction_interaction_contacts` many-to-many table instead.
  - **Interactions** A nullable `theme varchar(255)` column was added to the `interaction_interaction` table with possible values `'export'`, `'investment'`, `'other'` and NULL. This column is primarily for internal use.

# Data Hub API 11.9.0 (2019-04-23)

## Deprecations and removals

  - **Interactions** The deprecated `interaction_interaction.contact` column is being prepared for removal and will shortly be removed. Please use the `interaction_interaction_contacts` table instead.

## API

  - **Companies** `POST /v3/company` and `PATCH /v3/company/<uuid:pk>`: None values for address CharFields are now internally converted to empty strings as Django recommends: <https://docs.djangoproject.com/en/2.1/ref/models/fields/#null>

  - **Interactions** `GET /v3/interaction` and `GET /v3/interaction/<uid>`: The following fields were added:
    
      - `archived` - boolean - whether the interaction has been archived or not, defaults to `False`
      - `archived_on` - datetime string, nullable - the datetime at which the interaction was archived
      - `archived_by` - object, nullable - the Adviser that archived the interaction
      - `archived_reason` - string, nullable - free-form text explaining the reason for archiving the interaction
    
    These fields cannot be modified with PATCH or POST requests.
    
    Two additional API endpoints were added:
    
    `POST /v3/interaction/<uid>/archive` - requires a `"reason"` parameter. This will archive an interaction with the supplied reason.
    
    `POST /v3/interaction/<uid>/unarchive` This will 'un-archive' an interaction.

## Database schema

  - **Interactions** Four supporting fields were added to `interaction_interaction` for the purpose of allowing interactions to be archived:
      - `archived` (boolean, nullable)
      - `archived_on` (datetime string, nullable)
      - `archived_by_id` (uuid, nullable) - foreign key to `company_adviser`
      - `archived_reason` (string, nullable)
  - **Interactions** A supporting field was added to `interaction_interaction` for the purpose of logging the external source of an interaction:
      - `source` (JSONB, nullable)

# Data Hub API 11.8.0 (2019-04-16)

## Features

  - **Interactions** The first page of admin site tool for importing interactions was added, allowing a CSV file to be selected. This feature is currently behind the `admin-interaction-csv-importer` feature flag as it is incomplete.
  - **Investment** Large capital profiles can now be downloaded as a csv file

## Internal changes

  - The `cleanse_companies_using_worldbase_match` command now ignores matches for duns numbers already used in Data Hub as there can be only one Data Hub company record with a given duns number.

## API

  - **Interactions** `GET /v3/interaction` and `GET /v3/interaction/<uid>`: The following fields were added:
    
      - `status` - string - one of `'draft'` or `'complete'`, defaults to `'complete'`
      - `location` - string - free text representing the location of a meeting, defaults to `''`
    
    These can both modified with `PATCH` requests.
    
    When creating or updating an interaction whose `status='draft'`, both `service` and `communication_channel` are no longer required.

  - **Investment** The following endpoint has been added `/v4/search/large-investor-profile/export` to allow large capital profiles to be download as a csv file.
    
    The following data columns are returned per large capital profile in the csv (in this order):
    
      - Date created
      - Data Hub profile reference
      - Data Hub link
      - Investor company
      - Investor type
      - Investable capital
      - Global assets under management
      - Investor description
      - Required checks conducted
      - Required checks conducted by
      - Required checks conducted on
      - Deal ticket sizes
      - Asset classes of interest
      - Investment types
      - Minimum return rate
      - Time horizons
      - Restrictions
      - Construction risks
      - Minimum equity percentage
      - Desired deal roles
      - UK regions of interest
      - Other countries being considered
      - Notes on locations
      - Date last modified

## Database schema

  - **Interactions** Two supporting fields were added to `interaction_interaction` for the purpose of recording meetings:
      - `status` (text, nullable) - one of `"draft"` or `"complete"`
      - `location` (text, nullable) - free text representing the location of a meeting

# Data Hub API 11.7.0 (2019-04-11)

## Internal changes

  - A Django command was added to data cleanse some Data Hub companies using the D\&B Worldbase matches.

# Data Hub API 11.6.0 (2019-04-11)

## Deprecations and removals

  - **Interactions** `GET /v3/interaction`: The deprecated `dit_adviser__first_name` and `dit_adviser__last_name` values for the `sortby` query parameter were removed.

## Features

  - **Companies** Company match candidates can now be updated with a management command using data from CSV file

  - **Investment** The following fields have been added to Investment Search:
    
      - gross\_value\_added
    
    To allow `gross_value added` to be filtered by a range the following filters have been added:
    
      - gross\_value\_added\_start
      - gross\_value\_added\_end

  - **Investment** The following fields have been added to the investment csv download:
    
      - FDI type
      - Foreign equity investment
      - GVA multiplier
      - GVA

## Internal changes

  - **Investment** An investment project with a business activity of sales now uses the GVA Multiplier for retail to calculate Gross Value Added.
  - **Investment** New Django Admin page to update and add GVA Multipliers.
  - **Investment** Renamed command `populate_gross_value_addded` to `refresh_gross_value_added_values` and updated to include projects with a business activity of `sales` that do not have a sector.
  - `name.keyword`, `name.trigram` and `trading_names.trigram` sub-fields were added to the `company_field_with_copy_to_name_trigram` field type in all search models. These will replace the existing `name_trigram` and `trading_names_trigram` sub-fields and allow the type of the `name` sub-field to be changed from `keyword` to `text`.
  - Celery was updated to version 4.3.
  - Python was updated from version 3.6.8 to 3.7.2.

## API

  - **Investment** Investment project search endpoint `/v3/search/investment_project` now returns `gross_value_added` for each investment project.
    
    Search results can now be filtered by `gross_value_added` using the range filters `gross_value_added_start` and `gross_value_added_end`.

# Data Hub API 11.5.0 (2019-04-08)

## Features

  - **Interactions** Communication channel is now included in CSV exports of search results.
  - **Investment** `Gross Value Added` has been added to investment projects. This is calculated based on the sector, business activity and the projected foreign equity investment amount.

## Internal changes

  - `name.keyword` and `name.trigram` sub-fields were added to the `contact_or_adviser_field` field type in all search models. This is in preparation of the removal of the `name_trigram` sub-field, and also so we can change the type of the `name` sub-field from `keyword` to `text`.
  - Django was updated to version 2.2.

## API

  - **Events** `POST /v3/event, PATCH /v3/event/<id>`: The `organiser` field is now required.
  - **Investment** The following read only field has been added to `/v3/investment/` endpoint.
      - `gross_value_added`

## Database schema

  - **Investment** The database table `investment_investmentproject` has been updated with the following columns:
    
      - gross\_value\_added (decimal)
    
    The the following columns in database table `investment_gva_multiplier` has been updated:
    
      - `multiplier (float) not null` changed to `multiplier (decimal) not null`

# Data Hub API 11.4.1 (2019-04-04)

## Internal changes

  - **Investment** Fix for investment admin updated GVA multiplier string.

# Data Hub API 11.4.0 (2019-04-04)

## Deprecations and removals

  - **Interactions** `GET /metadata/service/`: The following values for the `contexts` field are deprecated and will be removed on or after 8 April 2019:
    
      - `interaction`
      - `service_delivery`
    
    Please see the API section for more details.

## Features

  - **Interactions** The following service contexts were added in Django admin:
    
      - Export interaction
      - Export service delivery
      - Investment interaction
      - Other interaction
      - Other service delivery
    
    All existing, non-disabled services with the 'Interaction' context have also been given the 'Other interaction' context.
    
    All existing, non-disabled services with the 'Service delivery' context have also been given the 'Other service delivery' context.
    
    The 'Interaction' context was renamed 'Interaction (deprecated)' and will be removed at a later date.
    
    The 'Service delivery' context was renamed 'Service delivery (deprecated)' and will be removed at a later date.

  - **Investment** A mapping from `Sectors` to `SIC Groupings` and `GVA Multiplier` information has been added. This mapping will be used to help calculate the GVA of an investment project.

  - The service contexts and team tags fields in the admin site were updated to use tick boxes for better usability.

  - A context filter was added to the service list in the admin site.

## API

  - **Interactions** `GET /metadata/service/`: The following values for the `contexts` field were added:
    
      - `export_interaction`
      - `export_service_delivery`
      - `investment_interaction`
      - `other_interaction`
      - `other_service_delivery`
    
    The following contexts are deprecated and will be removed on or after 8 April 2019:
    
      - `interaction`
      - `service_delivery`
    
    Please migrate to the new values above.

## Database schema

  - **Investment** The database table `investment_fdisicgrouping` has been added with the following columns:
    
      - id (uuid) not null,
      - name (text) not null,
      - disabled\_on (datetime),
    
    The database table `investment_gva_multiplier` has been added with the following columns:
    
      - id (uuid) not null,
      - multiplier (float) not null,
      - financial\_year (int) not null,
      - fdisicgrouping\_id (uuid) not null,
    
    Where `fdi_sicgrouping_id` is a foreign key to `investment_fdisicgrouping`.
    
    The database table `investment_investmentsector` has been added with the following columns:
    
      - sector\_id (uuid) not null pk,
      - fdi\_sicgrouping\_id (uuid) not null,
    
    Where `sector_id` is a foreign key to `metadata_sector` and `fdi_sicgrouping_id` is a foreign key to `investment_fdisicgrouping`.
    
    The database\_table `investment_investmentproject` has been updated and the following column has been added:
    
      - gva\_multiplier\_id (uuid),
    
    Where `gva_multiplier_id` is a foreign key to `investment_gvamultiplier`.

# Data Hub API 11.3.0 (2019-03-28)

## API

  - **Investment** The endpoint `/v4/large-capital-profile` now accepts and returns `required_checks_conducted_on` (date) and `required_checks_conducted_by` (adviser id).
    
    Both become required fields when `required_checks_conducted` is set to `Cleared` or `Issues identified`.

  - **Investment** New endpoint added `POST /v4/search/large-investor-profile` to search and retrieve large capital investor profiles.
    
    Profiles are filterable as follows. The following filters accept and single or list of ids:
    
      - id
      - asset\_classes\_of\_interest (metadata id)
      - country\_of\_origin (country id)
      - investor\_company (company id)
      - created\_by (adviser id)
      - investor\_type (metadata id)
      - required\_checks\_conducted (metadata id)
      - deal\_ticket\_size (metadata id)
      - investment\_type (metadata id)
      - minimum\_return\_rate (metadata id)
      - time\_horizon (metadata id)
      - restriction (metadata id)
      - construction\_risk (metadata id)
      - minimum\_equity\_percentage (metadata id)
      - desired\_deal\_role (metadata id)
      - uk\_region\_location (uk region id)
      - other\_countries\_being\_considered (country id)
    
    The following range filters have been added:
    
      - created\_on\_before (date)
      - created\_on\_after (date)
      - global\_assets\_under\_management\_start (int)
      - global\_assets\_under\_management\_end (int)
      - investable\_capital\_start (int)
      - investable\_capital\_end (int)
    
    The following text search filter has been added:
    
      - investor\_company\_name (text)

# Data Hub API 11.2.0 (2019-03-22)

## Deprecations and removals

  - **Interactions** `POST /v3/search/interaction`: The `dit_adviser` filter is deprecated and will be removed on or after 4 April 2019. Please use the `dit_participants__adviser` filter instead.
  - **Interactions** `POST /v3/search/interaction`: The `dit_adviser_name` filter is deprecated and will be removed on or after 4 April 2019. There is no replacement for this filter.
  - **Interactions** `GET /v3/search`, `POST /v3/search/interaction`: The `dit_adviser` and `dit_team` interaction fields are deprecated and will be removed on or after 28 March 2019. Please use `dit_participants` instead.
  - **Interactions** `POST /v3/search/interaction`: The `dit_team` filter is deprecated and will be removed on or after 4 April 2019. Please use the `dit_participants__team` filter instead.
  - **Investment** The column `investmentproject.likelihood_of_landing` was removed from the database.

## Features

  - **Interactions** A DIT participants section was added to the interaction form in the admin site. This displays all advisers and teams that are associated with an interaction. This section will remain read-only until the old DIT adviser and DIT team fields are removed from the database.
  - **Interactions** Global search is now aware of multiple interaction advisers and teams. This means that it searches the names of all advisers and teams added to an interaction instead of only one of them.
  - The 'My latest interactions' list on the home page is now aware of multiple interaction advisers. This means that if multiple advisers are added to an interaction, the interaction will show up on all of those advisers' home pages.

## Internal changes

  - **Investment** Large Capital investor profile search index added.
  - Various dependencies were updated.

## API

  - **Interactions** `POST /v3/search/interaction`: `dit_participants__adviser` was added as a filter. This is intended to replace the existing `dit_adviser` filter.
  - **Interactions** `POST /v3/search/interaction`: `dit_participants__team` was added as a filter. This is intended to replace the existing `dit_team` filter.

## Database schema

  - **Investment** The column `investmentproject.likelhood_of_landing` was removed from the database.

# Data Hub API 11.1.0 (2019-03-19)

## Deprecations and removals

  - **Interactions** `GET /v3/interaction`: The `dit_adviser__first_name` and `dit_adviser__last_name` values for the `sortby` query parameter are deprecated and will be removed on or after 28 March 2019.
  - **Interactions** `GET /v3/interaction, GET /v3/interaction/<id>, POST /v3/interaction, PATCH /v3/interaction/<id>`: The `dit_adviser` and `dit_team` fields are deprecated and will be removed on or after 28 March 2019. Please use `dit_participants` instead.
  - **Interactions** The DIT adviser and DIT team fields were temporarily made read-only in the admin site until the transition to allowing multiple advisers in an interaction is complete.
  - **Interactions** `interaction_interaction`: The `dit_adviser_id` and `dit_team_id` columns are deprecated and will be removed on or after 22 April 2019. Please use the `interaction_interactionditparticipant` table instead.

## API

  - **Interactions** `GET /v3/interaction, GET /v3/interaction/<id>, POST /v3/interaction, PATCH /v3/interaction/<id>`:
    
    `dit_participants` was added to responses. This is an array in the following format:
    
        [
            {
               "adviser": {
                   "id": ...,
                   "first_name": ...,
                   "last_name": ...,
                   "name": ...
               },
               "team": {
                   "id": ...,
                   "name": ...
               }
            },
            {
               "adviser": {
                   "id": ...,
                   "first_name": ...,
                   "last_name": ...,
                   "name": ...
               },
               "team": {
                   "id": ...,
                   "name": ...
               }
            },
            ...
        ]
    
    This field is intended to replace the `dit_adviser` and `dit_team` fields.

  - **Interactions** `POST /v3/interaction, PATCH /v3/interaction/<id>`:
    
    `dit_participants` is now a valid field in request bodies. This should be an array in the following format:
    
        [
            {
               "adviser": {
                   "id": ...
               }
            },
            {
               "adviser": {
                   "id": ...
               }
            },
            ...
        ]
    
    Note that the team for each participant will be set automatically. (If a team is provided it will be ignored.)
    
    `dit_participants` is intended to replace the `dit_adviser` and `dit_team` fields.

  - **Interactions** `GET /v3/search`, `POST /v3/search/interaction`:
    
    `dit_participants` was added to interaction search results in responses. This is an array in the following format:
    
        [
            {
               "adviser": {
                   "id": ...,
                   "first_name": ...,
                   "last_name": ...,
                   "name": ...
               },
               "team": {
                   "id": ...,
                   "name": ...
               }
            },
            {
               "adviser": {
                   "id": ...,
                   "first_name": ...,
                   "last_name": ...,
                   "name": ...
               },
               "team": {
                   "id": ...,
                   "name": ...
               }
            },
            ...
        ]
    
    This field is intended to replace the `dit_adviser` and `dit_team` fields.

# Data Hub API 11.0.0 (2019-03-15)

## Deprecations and removals

  - **Interactions** `GET,POST /v3/interaction`, `GET,PATCH /v3/interaction/<id>`: The deprecated `contact` field was removed. Please use `contacts` instead.
  - **Interactions** `GET /v3/search`, `POST /v3/search/interaction`: The deprecated `contact` field in interaction search results was removed. Please use `contacts` instead.

## Features

  - **Investment** A new endpoint has been added for creating and maintaining Large capital investor profiles on datahub.

## Internal changes

  - **Interactions** A Celery task was added to create `InteractionDITParticipant` objects from the `dit_adviser` and `dit_team` values for interactions that do not already have a `InteractionDITParticipant` object. The task must be run manually.

## API

  - **Investment** `GET /v4/large-investor-profile` returns a list of all the large capital profiles. The results can be filtered using a parameter of `investor_company_id` given a company id.
    
    `POST /v4/large-investor-profile` creates a large capital profile for a given `investor_company`.
    
    `GET /v4/large-investor-profile/<uuid:pk>` returns the large capital profile for the given id.
    
    `PATCH /v4/large-investor-profile/<uuid:pk>` updates the large capital profile for the given id.
    
      - A large capital profile consists of the following fields:  
        `id` the uuid of the of the investor profile (readonly),
        
        `investor_company` a company (uuid and name),
        
        `investor_type` the capital investment investor type (uuid and name),
        
        `investable_capital` the capital that could be invested in USD (int),
        
        `global_assets_under_management` Global assets under management amount in USD (int),
        
        `investor_description` a text description of the investor,
        
        `required_checks_conducted` a required background checks conducted status (uuid and name),
        
        `deal_ticket_sizes` a list of deal ticket sizes (uuid and name),
        
        `investment_types` a list of large capital investment types (uuid and name),
        
        `minimum_return_rate` a return rate (uuid and name),
        
        `time_horizons` a list of time horizons (uuid and name),
        
        `construction_risks` a list of construction risks (uuid and name),
        
        `minimum_equity_percentage` an equity percentage (uuid and name),
        
        `desired_deal_roles` a list of desired deal roles (uuid and name),
        
        `restrictions` a list of restrictions (uuid and name),
        
        `asset_classes_of_interest` a list of asset class interests (uuid and name),
        
        `uk_region_locations` a list of uk regions (uuid and name),
        
        `notes_on_locations` a text field,
        
        `other_countries_being_considered` a list of countries (uuid and name),
        
        `created_on` the time and date the profile was created,
        
        `modified_on` the time and date the profile was last modified,
        
        `incomplete_details_fields` a list of the detail fields that are yet to have a value set.
        
        `incomplete_requirements_fields` a list of the requirements fields that are yet to have a value set.
        
        `incomplete_location_fields` a list of the location fields that are yet to have a value set.
    
      - The detail fields:  
        `investor_type`
        
        `investable_capital`,
        
        `global_assets_under_management`,
        
        `investor_description`,
        
        `background_checks_conducted`
    
      - The requirement fields:  
        `deal_ticket_sizes`,
        
        `investment_types`,
        
        `minimum_return_rate`,
        
        `time_horizons`,
        
        `construction_risks`,
        
        `minimum_equity_percentage`,
        
        `desired_deal_roles`,
        
        `restrictions`,
        
        `asset_classes_of_interest`
    
      - The location fields:  
        `uk_region_locations`,
        
        `notes_on_locations`,
        
        `other_countries_being_considered`

  - **Investment** The following metadata endpoints have been added
    
    `GET /metadata/capital-investment/asset-class-interest/` returns all possible `asset_class_interest` values. The values also include a field `asset-class-interest-sector` which returns the `id` and `name` of the the associated `asset_class_interest_sector`.
    
    `GET /metadata/capital-investment/required-checks-conducted/` returns all possible `investor_profile_requiredchecksconducted` values.
    
    `GET /metadata/capital-investment/construction-risk/` returns all possible `investor_profile_constructionrisk` values.
    
    `GET /metadata/capital-investment/deal-ticket-size/` returns all possible `investor_profile_dealticketsize` values.
    
    `GET /metadata/capital-investment/desired-deal-role/` returns all possible `investor_profile_desireddealrole` values.
    
    `GET /metadata/capital-investment/equity-percentage/` returns all possible `investor_profile_equitypercentage` values.
    
    `GET /metadata/capital-investment/investor-type/` returns all possible `investor_profile_investortype` values.
    
    `GET /metadata/capital-investment/large-capital-investment-type/` returns all possible `investor_profile_largecapitalinvestmenttype` values.
    
    `GET /metadata/capital-investment/restriction/` returns all possible `investor_profile_restriction` values.
    
    `GET /metadata/capital-investment/return-rate/` returns all possible `investor_profile_returnrate` values.
    
    `GET /metadata/capital-investment/time-horizon/` returns all possible `investor_profile_time_horizon` values.

## Database schema

  - **Interactions** The table `interaction_interactionditparticipant` table was added with the following columns:
    
      - `"id" bigserial NOT NULL PRIMARY KEY`
      - `"adviser_id" uuid NULL`
      - `"interaction_id" uuid NOT NULL`
      - `"team_id" uuid NULL`
    
    This is a many-to-many relationship table linking interactions with advisers.
    
    The table had not been fully populated with data yet; continue to use `interaction_interaction.dit_adviser_id` and `interaction_interaction.dit_team_id` for the time being.

# Data Hub API 10.5.0 (2019-03-11)

## Deprecations and removals

  - **Interactions** `GET /v3/interaction`: The deprecated `contact__first_name` and `contact__last_name` values for the `sortby` query parameter were removed.
  - **Interactions** `GET /v3/interaction`: The deprecated `contact_id` query parameter was removed. Please use `contacts__id` instead.
  - **Interactions** `POST /v3/search/interaction`: The deprecated `contact` and `contact_name` filters were removed.
  - **Interactions** `POST /v3/search/interaction`: The deprecated `contact.name`, `dit_adviser.name`, `dit_team.name` and `id` values for the `sortby` query parameter were removed.
  - `GET /v3/search`: all the values for the `sortby` query parameter were removed.

## Internal changes

  - **Investment** Fix for `generate_spi_report` celery task having the incorrect path.

## Database schema

  -   - **Investment** The database table `investor_profile_investorprofile` has been added with the following columns:  
        `id (uuid) not null`,
        
        `investor_company_id (uuid) not null`,
        
        `profile_type_id (uuid) not null`,
        
        `created_on (timestamp)`,
        
        `modified_on (timestamp)`,
        
        `created_by_id (uuid)`,
        
        `modified_by_id (uuid)`,
        
        `global_assets_under_management (numeric)`,
        
        `investable_capital (numeric)`,
        
        `investor_description (text)`,
        
        `notes_on_locations (text)`,
        
        `investor_type_id (uuid)`,
        
        `minimum_equity_percentage_id (uuid)`,
        
        `minimum_return_rate_id (uuid)`,
        
        `required_checks_conducted_id (uuid)`.

  -   - **Investment** The following metadata database tables have been added:  
        `investor_profile_assetclassinterestsector`
        
        `investor_profile_backgroundchecksconducted`
        
        `investor_profile_constructionrisk`
        
        `investor_profile_dealticketsize`
        
        `investor_profile_desireddealrole`
        
        `investor_profile_equitypercentage`
        
        `investor_profile_investortype`
        
        `investor_profile_largecapitalinvestmenttype`
        
        `investor_profile_restriction`
        
        `investor_profile_returnrate`
        
        `investor_profile_timehorizon`
    
      - Each table has the following columns:  
        `id (uuid) not null`,
        
        `name (text) not null`,
        
        `order (float) not null`.
    
      - The metadata table `investor_profile_assetclassinterest` has the columns:  
        `id (uuid) not null`,
        
        `name (text) not null`,
        
        `order (float) not null`,
        
        `asset_class_interest_sector_id (uuid) not null`.

# Data Hub API 10.4.0 (2019-03-07)

## Deprecations and removals

  - **Companies** The `contacts` field in company search results was removed from the following endpoints:
    
      - `/v3/search`
      - `/v3/search/company`
      - `/v4/search/company`
    
    If you require a list of contacts for a company, please use `/v3/contacts?company_id=<company ID>`

## Features

  - Chinese administrative areas were added.

## Bug fixes

  - **Advisers** The adviser autocomplete feature no longer returns an error when certain non-ASCII characters such as é are entered.

## Internal changes

  - **Companies** Previously squashed migrations were removed.
  - **Investment** The subdirectory `project` has been added to the investment django application and all investment project related code moved to it and all import paths updated.
  - Various dependencies were updated.

## API

  - **Companies** `GET /v4/public/company/<id>` was added as a Hawk-authenticated endpoint for retrieving a single company. This is similar to `GET /v4/company/<id>` but has a slightly reduced set of fields.
  - **Companies** `POST /v4/public/search/company` was added as a Hawk-authenticated company search endpoint. This is similar to `POST /v4/search/company` but has a reduced set of filters (`name`, `archived` and `original_query`) and slightly reduced set of response fields.

# Data Hub API 10.3.0 (2019-02-27)

## Deprecations and removals

  - **Companies** `POST /v3/search/company`, `POST /v3/search/company/export` the following filters were deleted:
      - `description`
      - `export_to_country`
      - `future_interest_country`
      - `global_headquarters`
      - `sector`
      - `trading_address_country`
  - **Companies** `POST /v3/search/company`, `POST /v3/search/company/export` the following sortby values were deleted:
      - `archived`
      - `archived_by`
      - `business_type.name`
      - `companies_house_data.company_number`
      - `company_number`
      - `created_on`
      - `employee_range.name`
      - `headquarter_type.name`
      - `id`
      - `registered_address_town`
      - `sector.name`
      - `trading_address_town`
      - `turnover_range.name`
      - `uk_based`
      - `uk_region.name`
  - **Interactions** `POST /v3/search/interaction`: The `dit_adviser.name`, `dit_team.name` and `id` values for the `sortby` query parameter are deprecated and will be removed on or after 28 February 2019.
  - **Investment** The field `InvestmentProject.likelihood_of_landing` was removed from django.
  - `GET /v3/search`: all the values for the `sortby` query parameter are deprecated and will be removed on or after 28 February 2019.

## Features

  - **Companies** Company merge tool now supports merging companies having OMIS orders.

## Internal changes

  - **Companies** The companieshouse company search endpoints now use the nested registered address object when searching by term.
  - The django app `leads` was deleted.

# Data Hub API 10.2.0 (2019-02-21)

## Deprecations and removals

  - **Companies** The endpoint `/v3/search/companieshousecompany` is deprecated and will be removed on or after the 28th of February, please use v4 instead.

## Features

  - **Companies** Company merge tool now supports merging companies having investment projects.
  - Administrative areas of countries were added to the admin site. These cannot be edited and will initially be used by the Market Access service (but are not used within Data Hub CRM at present).

## Internal changes

  - **Companies** The search logic is now using company address and registered address instead of trading address behind the scenes.

## API

  - **Companies** API V4 of companieshouse company search was introduced with nested object format for addresses. The endpoint `/v4/search/companieshousecompany` was added with the `registered_address_*` fields replaced by the nested object `registered_address`.
  - `GET /metadata/administrative-area/` was added to retrieve a list of administrative areas of countries.
  - `/metadata/country/`: `overseas_region` was added to each country in responses. For non-UK countries, this is an object containing the the ID and name of the DIT overseas region the country belongs to.

## Database schema

  - The `metadata_administrative_area` table was added with columns `("disabled_on" timestamp with time zone NULL, "id" uuid NOT NULL PRIMARY KEY, "name" text NOT NULL, "country_id" uuid NOT NULL)`.
    
    This contains a list of administrative areas of countries.

# Data Hub API 10.1.0 (2019-02-19)

## Deprecations and removals

  - **Companies** The `contacts` field in company search results is deprecated and will be removed on or after 28 February 2019 from the following endpoints:
      - `/v3/search`
      - `/v3/search/company`
      - `/v4/search/company`

## Internal changes

  - **Companies** `company.address_country_id` and `company.registered_address_country_id` are now indexed in ElasticSearch so that they can be used when filtering down results.
  - Various dependencies were updated.

# Data Hub API 10.0.0 (2019-02-18)

## Deprecations and removals

  - **Advisers** `GET /adviser/`: The `first_name`, `first_name__icontains`, `last_name`, `last_name__icontains`, `email` and `email__icontains` query parameters are deprecated and will be removed on or after 4 March 2019.
  - **Companies** The following endpoints are deprecated and will be removed on or after the 28th of February, please use v4 instead:
      - `/v3/search/company`
      - `/v3/search/company/autocomplete`
      - `/v3/search/company/export`
  - **Companies** The field `trading_name` was removed from the endpoints below, please use the `trading_names` field instead:
      - `/v3/search/company`
      - `/v3/search/company/autocomplete`
      - `/v3/search/contact`: from the nested company object
      - `/v3/search/interaction`: from the nested company object
      - `/v3/search/order`: from the nested company object

## Features

  - **Interactions** Policy issue types, policy areas and policy feedback notes were added to interaction search result CSV exports.

## API

  - **Advisers** This adds a new `autocomplete` query parameter to `GET /adviser/` intended to replace the previous name-related query parameters.
    
    The new parameter matches prefixes of words in the `first_name`, `last_name` and `dit_team.name` fields. Each token must match the prefix of at least one word in (at least) one of those fields.
    
    Results are automatically ordered with advisers with a match on `first_name` appearing first, `last_name` second and `dit_team.name` last.
    
    As a result, the `first_name`, `first_name__icontains`, `last_name`, `last_name__icontains`, `email` and `email__icontains` query parameters are deprecated and will be removed on or after 4 March 2019.

  - **Companies** API V4 for company search was introduced with nested object format for addresses. The following endpoints were added:
    
      - `/v4/search/company`: see below
      - `/v4/search/company/autocomplete`: see below
      - `/v4/search/company/export`: same response body as v3
    
    `/v4/search/company`, `/v4/search/company/autocomplete`:
    
      - The `trading_address_*` fields were removed from v4
      - The `registered_address_*` fields were replaced by the nested object `registered_address`
      - The nested object `address` was added. Its data was populated from trading\_address fields or registered\_address whichever was defined.

  - **Companies** The field `trading_name` was removed from the endpoints below, please use the `trading_names` field instead:
    
      - `/v3/search/company`
      - `/v3/search/company/autocomplete`
      - `/v3/search/contact`: from the nested company object
      - `/v3/search/interaction`: from the nested company object
      - `/v3/search/order`: from the nested company object

# Data Hub API 9.10.0 (2019-02-14)

## Deprecations and removals

  - **Companies** The following endpoints are deprecated and will be removed on or after the 21st of February, please use v4 instead:
      - `/v3/ch-company`
      - `/v3/ch-company/<uuid:pk>`
  - **Companies** The following endpoints are deprecated and will be removed on or after the 21st of February, please use v4 instead:
      - `/v3/company`
      - `/v3/company/<uuid:pk>`
      - `/v3/company/<uuid:pk>/archive`
      - `/v3/company/<uuid:pk>/audit`
      - `/v3/company/<uuid:pk>/one-list-group-core-team`
      - `/v3/company/<uuid:pk>/timeline`
      - `/v3/company/<uuid:pk>/unarchive`
  - **Companies** `POST /v3/search/company`, `POST /v3/search/company/export` the following filters are deprecated and will be removed on or after the 21st of February:
      - `description`
      - `export_to_country`
      - `future_interest_country`
      - `global_headquarters`
      - `sector`
      - `trading_address_country`
  - **Companies** `POST /v3/search/company`, `POST /v3/search/company/export` the following sortby values are deprecated and will be removed on or after the 21st of February:
      - `archived`
      - `archived_by`
      - `business_type.name`
      - `companies_house_data.company_number`
      - `company_number`
      - `created_on`
      - `employee_range.name`
      - `headquarter_type.name`
      - `id`
      - `registered_address_town`
      - `sector.name`
      - `trading_address_town`
      - `turnover_range.name`
      - `uk_based`
      - `uk_region.name`
  - **Companies** The following database fields are deprecated and will be removed on or after the 21st of February, please use the `address_*` fields instead:
      - `trading_address_1`
      - `trading_address_2`
      - `trading_address_town`
      - `trading_address_county`
      - `trading_address_postcode`
      - `trading_address_country_id`
  - **Companies** The field `trading_name` was removed from all `/v3/company/*` and `/v4/company/*` endpoints, please use the `trading_names` field instead.

## Features

  - **Companies** Companies now define fields for a mandatory address representing the main location for the business and fields for an optional registered address. Trading address fields are still automatically updated but deprecated. The data was migrated in the following way:
      - address fields: populated from trading address or (as fallback) registered address in this specific order.
      - registered fields: kept untouched for now but will be overridden by the values from Companies House where possible or (as fallback) set to blank values. A deprecation notice will be announced before this happens.
  - **Interactions** Global search was updated to handle multiple interaction contacts correctly when matching search terms with interactions.
  - **Investment** A note can now be submitted with any change to an Investment Project.

## Bug fixes

  - **Interactions** A performance problem with the interaction list in the admin site was resolved.

## Internal changes

  - The permissions and content type for the previously deleted businesslead model/table were also deleted.
  - Django was updated from 2.1.5 to 2.1.7.

## API

  - **Advisers** `GET /adviser/`: `is_active` was added as a query parameter. This is a boolean filter that filters advisers by whether they are active or not.

  - **Companies** API V4 for companies house companies was introduced with nested object format for registered address. The `registered_address_*` fields were replaced by the nested object `registered_address` for the following endpoints:
    
      - `/v4/ch-company`
      - `/v4/ch-company/<uuid:pk>`
    
    The nested object has the following contract:
    
        'line_1': '2',
        'line_2': 'Main Road',
        'town': 'London',
        'county': 'Greenwich',
        'postcode': 'SE10 9NN',
        'country': {
            'id': '80756b9a-5d95-e211-a939-e4115bead28a',
            'name': 'United Kingdom',
        }

  - **Companies** `/v4/company`, `/v4/company/<uuid:pk>`, `/v4/company/<uuid:pk>/archive`, `/v4/company/<uuid:pk>/unarchive`:
    
      - The `trading_address_*` fields were removed from v4
      - The `registered_address_*` fields were replaced by the nested object `registered_address` and made optional
      - The nested object `address` was added and is mandatory when creating a company. Its data was populated from trading\_address fields or registered\_address whichever was defined.
      - The nested `companies_house_data` object was removed from v4

  - **Companies** API V4 for companies was introduced with nested object format for addresses. A new prefix `v4` was introduced along with the following endpoints:
    
      - `/v4/company`: see the related news fragment
      - `/v4/company/<uuid:pk>`: see the related news fragment
      - `/v4/company/<uuid:pk>/archive`:see the related news fragment
      - `/v4/company/<uuid:pk>/unarchive`: see the related news fragment
      - `/v4/company/<uuid:pk>/audit`: same response body as v3
      - `/v4/company/<uuid:pk>/one-list-group-core-team`: same response body as v3
      - `/v4/company/<uuid:pk>/timeline`: same response body as v3
    
    The nested object has the following contract:
    
        'line_1': '2',
        'line_2': 'Main Road',
        'town': 'London',
        'county': 'Greenwich',
        'postcode': 'SE10 9NN',
        'country': {
            'id': '80756b9a-5d95-e211-a939-e4115bead28a',
            'name': 'United Kingdom',
        }

  - **Companies** `GET /v3/search/company/autocomplete`: the query param `term` is now required.

  - **Companies** The field `trading_name` was removed from all `/v3/company/*` and `/v4/company/*` endpoints, please use the `trading_names` field instead.

  - **Investment** `POST /v3/investment` endpoint now accepts `note` as an optional property that can be set whilst creating an investment project. The property expects a dictionary with a mandatory field of `text` and an optional field of `activity_type`. `activity_type` expects a `investment_activity_type` id.
    
    `PATCH /v3/investment/<uuid:pk>` endpoint now accepts `note` as an optional property that can be set whilst updating an investment project. The property expects a dictionary with a mandatory field of `text` and an optional field of `activity_type`. `activity_type` expects a `investment_activity_type` id.
    
    `GET /v3/investment/<uuid:pk>/audit` endpoint now returns a property `note` within each audit change entry.
    
    New endpoint `GET /metadata/investment-activity-type/` added that returns all possible `investment_activity_type` options.

## Database schema

  - **Companies** The following columns in the `company_companieshousecompany` table were made NOT NULL:
    
      - `registered_address_2`
      - `registered_address_county`
      - `registered_address_country_id`
      - `registered_address_postcode`

  - **Companies** The following database fields are deprecated and will be removed on or after the 21st of February, please use the `address_*` fields instead:
    
      - `trading_address_1`
      - `trading_address_2`
      - `trading_address_town`
      - `trading_address_county`
      - `trading_address_postcode`
      - `trading_address_country_id`

  - **Investment** The table `investment_investmentactivitytype` has been added. The values of the column `name` will initial be `change`, `risk`, `issue`, `SPI Interaction` and `Internal Interaction`.
    
    The table `investment_investmentactivity` has been added. The columns are `id`, `investment_project_id`, `revision_id`, `activity_type_id` and `text`. Where `revision_id` is a link to a copy of the investment projects data at the time of adding the row. Where `text` can be used as a note to be associated with a change to a project or as a way to detail an activity on the project.

# Data Hub API 9.9.0 (2019-02-07)

## Deprecations and removals

  - **Interactions** `POST /v3/search/interaction`: The `contact` and `contact_name` filters in request bodies are deprecated and will be removed on or after 28 February 2019.
  - **Interactions** `GET /v3/search`, `POST /v3/search/interaction`: The `contact` field in responses is deprecated and will be removed on or after 28 February 2019. Please use `contacts` instead.
  - **Interactions** `POST /v3/search/interaction`: The `contact.name` value for the `sortby` query parameter is deprecated and will be removed on or after 28 February 2019.
  - **Interactions** `GET /v3/interaction`: The `contact__first_name` and `contact__last_name` values for the `sortby` query parameter are deprecated and will be removed on or after 28 February 2019. Please use `first_name_of_first_contact` and `last_name_of_first_contact` instead for event service deliveries only.

## Features

  - **Contacts** The contact search CSV export was updated to handle interactions with multiple contacts for the 'Date of latest interaction' and 'Team of latest interaction' fields.
  - **Contacts** Contacts can now be sorted by name in the admin site.
  - **Interactions** The admin site now uses an autocomplete widget for the contacts field when editing or adding an interaction.
  - **Interactions** The search CSV export was updated to handle interactions with multiple contacts. The previous Contact and Job title columns have been merged into a single Contacts column. This column contains the names of all the contacts for each interaction with the job title in brackets after each name and a comma between contacts.

## Internal changes

  - **Companies** The system is now using the address and registered address for internal business logic instead of the trading and registered address.
  - A management command to delete all Elasticsearch indices matching the configured index name prefix was added. This is intended for use on GOV.UK PaaS when required as GOV.UK PaaS Elasticsearch does not allow deletions using wildcards.
  - A management command to run MI Dashboard pipeline if changes to the relevant models have been made was added.
  - Updated various dependencies.

## API

  - **Interactions** `GET /v3/search`, `POST /v3/search/interaction`: `contacts` was added as an array field in search results. This field is intended to replace the `contact` field. The `contact` field is deprecated and will be removed on or after 28 February 2019.

  - **Interactions** `GET /v3/interaction`: `first_name_of_first_contact` and `last_name_of_first_contact` were added as `sortby` query parameter values for sorting event service deliveries by the first or last name of the contact. These sorting options aren't intended to be used for other types of interaction which may have multiple contacts.
    
    The `contact__first_name` and `contact__last_name` sorting options are deprecated and will be removed on or after 28 February 2019.

# Data Hub API 9.8.0 (2019-02-04)

## Deprecations and removals

  - **Interactions** `GET,POST /v3/interaction`, `GET,PATCH /v3/interaction/<id>`: The `contact` field is deprecated and will be removed on or after 24 February 2019. Please use `contacts` instead.
  - **Interactions** The `interaction_interaction.contact_id` column is deprecated and will be removed on or after 4 March 2019. Please use the `interaction_interaction_contacts` many-to-many table instead.
  - **Interactions** `GET /v3/interaction`: The `contact_id` query parameter is deprecated and will be removed on or after 24 February 2019. Please use `contacts__id` instead.

## Features

  - **Interactions** The admin site now displays multiple contacts for interactions.

## API

  - **Interactions** `POST /v3/interaction`, `PATCH /v3/interaction/<id>`: Additional validation was added to make sure that all `contacts` belong to the specified `company`. This validation only occurs when an interaction is created, or the `contacts` or `company` field is updated.
  - **Interactions** `GET,POST /v3/interaction`, `GET,PATCH /v3/interaction/<id>`: `contacts` was added as an array field to replace the `contact` field. The `contact` and `contacts` field will mirror each other (except that `contact` will only return a single contact). The `contact` field is deprecated and will be removed on or after 24 February 2019.
  - **Interactions** `GET /v3/interaction`: `contacts__id` was added as a query parameter to support filtering by contact ID for interactions with multiple contacts. The previous `contact_id` filter is deprecated and will be removed on or after 24 February 2019.

## Database schema

  - **Interactions** The `interaction_interaction.contact_id` column is deprecated and will be removed on or after 4 March 2019. Please use the `interaction_interaction_contacts` many-to-many table instead.

# Data Hub API 9.7.0 (2019-01-29)

## Features

  - The MI dashboard pipeline task now loads all investment projects instead of only for current financial year.

## Internal changes

  - **Companies** A celery task to populate company address fields from trading and registered address fields was added to allow data to be migrated.
  - The MI dashboard pipeline was rescheduled to run at around 1 AM each night.
  - Various dependencies were updated.

# Data Hub API 9.6.0 (2019-01-24)

## Database schema

  - **Companies** The following fields were added:
    
    `"address_1" varchar(255)`
    
    `"address_2" varchar(255)`
    
    `"address_country_id" uuid`
    
    `"address_county" varchar(255)`
    
    `"address_postcode" varchar(255)`
    
    `"address_town" varchar(255)`
    
    The system will be migrated from using the `registered_address_*` and `trading_address_*` fields to `address_*` (main location for the business) and `registered_address_*` (official address) fields instead. However, you should not use the new address fields yet and migration steps will be communicated in future release notes.

  - **Interactions** The table `interaction_interaction_contacts` table with columns `("id" serial NOT NULL PRIMARY KEY, "interaction_id" uuid NOT NULL, "contact_id" uuid NOT NULL)` was added.
    
    This is a many-to-many table linking interactions with contacts.
    
    The table had not been fully populated with data yet; continue to use `interaction_interaction.contact_id` for the time being.

# Data Hub API 9.5.0 (2019-01-22)

## Deprecations and removals

  - **Companies** The column `company_company.alias` was deleted from the database.

## Features

  - **OMIS** Search response for OMIS orders now contains total subtotal cost for given query.

## Bug fixes

  - The MI dashboard pipeline now correctly selects the investment projects for given fiscal year.
  - Country URL in the MI dashboard is now assembled correctly.

## API

  - **OMIS** `POST /v3/search/order`: The response now contains `summary` property that includes a total value of filtered orders' subtotal cost (`total_subtotal_cost`)\`.

## Database schema

  - **Companies** The column `company_company.alias` was deleted from the database.

# Data Hub API 9.4.0 (2019-01-21)

## Internal changes

  - `country_url` in the MI dashboard pipeline is now formatted correctly.

## API

  - **Interactions** `POST /v3/interaction`: `was_policy_feedback_provided` can no longer be omitted when creating interactions.

## Database schema

  - **Companies** The column `company_company.trading_names` was made NOT NULL.
  - **Interactions** The `interaction_interaction.policy_feedback_notes` column is now non-nullable. (An empty string is used for blank values.)
  - **Interactions** The `interaction_interaction.was_policy_feedback_provided` column is now non-nullable.

# Data Hub API 9.3.0 (2019-01-17)

## Deprecations and removals

  - **Companies** The field `Company.alias` was removed from django.
  - **Companies** `PATCH /v3/company/<uuid:pk>`: the PATCH string field `trading_name` is deprecated and will be removed on or after January 24. Please use the array field `trading_names` instead.
  - **Interactions** The `interaction_interaction.policy_issue_type_id` column was deleted from the database.
  - **Investment** `POST /v3/search/investment_project`: The `aggregations` property of responses was removed.
  - The table `metadata_companyclassification` was deleted.

## API

  - **Companies** `PATCH /v3/company/<uuid:pk>`: when updating trading names, the PATCH array field `trading_names` should be used instead of the deprecated string field `trading_name`.
  - **Interactions** `GET /v3/search`, `POST /v3/search/interaction`: `policy_areas` was added to interaction search results.
  - **Interactions** `POST /v3/search/interaction`: `policy_areas` was added as a filter, accepting one or more policy area IDs that results should match one of.
  - **Interactions** `GET /v3/search`, `POST /v3/search/interaction`: `policy_issue_types` was added to interaction search results.
  - **Interactions** `POST /v3/search/interaction`: `policy_issue_types` was added as a filter, accepting one or more policy issue type IDs that results should match one of.
  - **Investment** `POST /v3/search/investment_project`: The `aggregations` property of responses was removed.

## Database schema

  - **Interactions** The `interaction_interaction.policy_issue_type_id` column was deleted from the database.
  - The table `metadata_companyclassification` was deleted.

# Data Hub API 9.2.0 (2019-01-15)

## Internal changes

  - It is now possible to specify the location of SSL CA certificates for Django Redis cache client. Environment variable `REDIS_SSL_CA_CERTS_PATH` defaults to '/etc/ssl/certs/ca-certificates.crt'.

## API

  - **Investment** `POST /v3/investment` endpoint now accepts `project_manager_request_status` as an optional property that can be set whilst creating an investment project. The property expects a `investment_projectmanagerrequeststatus` id.
    
    `GET /v3/investment/<uuid:pk>` endpoint now includes `project_manager_request_status` and read-only field `project_manager_requested_on` in the response.
    
    `PATCH /v3/investment/<uuid:pk>` endpoint now accepts `project_manager_request_status` as an optional property that can be set whilst updating an investment project. The property expects a `investment_projectmanagerrequeststatus` id.
    
    New endpoint `GET /metadata/project-manager-request-status/` added that returns all possible `project_manager_request_status` options.

## Database schema

  - **Investment** The columns `project_manager_request_status (uuid NULL)` and `project_manager_requested_on (timestamp NULL)` were added to the table `investment_investmentproject`.
    
    The table `investment_projectmanagerrequeststatus` has been added.

# Data Hub API 9.1.0 (2019-01-14)

## Deprecations and removals

  - **Interactions** The 'Policy feedback' service is no longer created in new environments.
  - **Interactions** `GET /v3/interaction, GET /v3/interaction/<id>`: `policy_issue_type` was removed from responses.

## Internal changes

  - Python was updated from version 3.6.7 to 3.6.8 in deployed environments.

## API

  - **Interactions** `GET /v3/interaction, GET /v3/interaction/<id>`: `policy_issue_type` was removed from responses.

# Data Hub API 9.0.1 (2019-01-10)

## Bug fixes

  - A bug for audit history where a related entity has a null value and cannot be iterated over was fixed.

# Data Hub API 9.0.0 (2019-01-10)

## Deprecations and removals

  - **Companies** The column `company_company.classification_id` was removed from the database.
  - **Interactions** Policy feedback permissions relating to the legacy version of the policy feedback feature were removed.
  - **Interactions** `POST /v3/interaction`: `"policy_feedback"` is no longer accepted as a value for the `kind` field.
  - **Investment** `POST /v3/search/investment_project`: The `aggregations` property of responses is deprecated and will be removed on or after 17 January 2019.
  - The model `metadata.CompanyClassification` was removed from the django definition and the django admin. The related database table will be deleted with the next release.
  - `GET /v3/search`: `companieshousecompany` is now correctly not accepted in the `entity` parameter, and not included in the returned `aggregations` array. (Previously, specifying `companieshousecompany` in the `entity` parameter caused all search models to be searched.) If you want to search Companies House companies, please use `/v3/search/companieshousecompany` instead.

## Features

  - **OMIS** Less than or equal to and greater than or equal to filters were added for the completed on field to OMIS order search.
  - **OMIS** Less than or equal to and greater than or equal to filters were added for the delivery date field to OMIS order search.

## Internal changes

  - **Companies** The value of the model field `alias` is now ignored and the `trading_name` API field now gets and saves its value from/into the model field `trading_names` instead.
  - **Investment** All nested fields were replaced with object fields in the investment project search model for improved maintainability and performance.
  - The app `dnb_match` and the tables `dnb_match_dnbmatchingresult`, `dnb_match_dnbmatchingcsvrecord` were created to support the D\&B matching pieces of work. At this stage, they are to be considered private and not to be used as they may be temporary and can change without notice.
  - All nested fields were replaced with object fields in the Companies House company search model for improved maintainability and performance.
  - The option to synchronise single objects to Elasticsearch using the thread pool was removed. Celery is now used in all cases.
  - Various dependencies were updated.
  - Optimisations were made to the search models so improve performance when sorting by text fields and make the sorting order more logical in some cases.

## API

  - **Companies** GET `/v3/company/<uuid:pk>/audit` now returns string representation of any changes made to related objects rather than ids.
  - **Contacts** GET `/v3/contact/<uuid:pk>/audit` now returns string representation of any changes made to related objects rather than ids.
  - **Interactions** `POST: /v3/interaction`: `"policy_feedback"` is no longer accepted as a value for the `kind` field.
  - **Investment** `POST /v3/search/investment_project`: The `aggregations` property of responses is deprecated and will be removed on or after 17 January 2019.
  - **Investment** GET `/v3/investment/<uuid:pk>/audit` now returns string representation of any changes made to related objects rather than ids.
  - **OMIS** `POST /v3/search/order`: `completed_on_before` and `completed_on_after` filters were added. These only accept dates without a time component. Timestamps on the dates specified will be included in the results.
  - **OMIS** `POST /v3/search/order`: `delivery_date_before` and `delivery_date_after` filters were added.
  - `GET /v3/search`: `companieshousecompany` is now correctly not accepted in the `entity` parameter, and not included in the returned `aggregations` array. (Previously, specifying `companieshousecompany` in the `entity` parameter caused all search models to be searched.) If you want to search Companies House companies, please use `/v3/search/companieshousecompany` instead.

## Database schema

  - **Companies** The column `company_company.classification_id` was removed from the database.

# Data Hub API 8.7.0 (2019-01-03)

## Deprecations and removals

  - **Companies** The field `classification` was removed from the django definition and the related database column will be deleted with the next release.

## Features

  - **OMIS** `Lead adviser` is now available in the OMIS CSV extract.

## Internal changes

  - **Companies** All nested fields were replaced with object fields in the company search model for improved maintainability and performance.
  - **Contacts** All nested fields were replaced with object fields in the contact search model for improved maintainability and performance.
  - **Events** All nested fields were replaced with object fields in the event search model for improved maintainability and performance.
  - **OMIS** OMIS order invoices can now be viewed and searched for by invoice number and order reference in the admin site.
  - **OMIS** All nested fields were replaced with object fields in the OMIS order search model for improved maintainability and performance.
  - **OMIS** OMIS orders can now be searched for by the current invoice number for the order in the admin site.

# Data Hub API 8.6.0 (2018-12-31)

## Internal changes

  - The performance of the `migrate_es` and `sync_es` management commands was improved in some cases by the use of prefetching for to-many fields.
  - The `migrate_es` and `sync_es` management commands were modified to avoid the use of stale data when copying data to Elasticsearch.

# Data Hub API 8.5.0 (2018-12-27)

## Deprecations and removals

  - All sorting options and filters in Companies House company search were removed as these were not being used by any client.

## Features

  - **Investment** Following fields in `mi` database have got their default values changed:
      - `sector_name` now has `No Sector assigned` default when source field has no value
      - `possible_uk_region_names` now has `No UK region assigned` default when source field has no value
      - `actual_uk_region_names` now has `No UK region assigned` default when source field has no value
      - `uk_region_name` now has `No UK region assigned` default when source fields have no value
      - `investor_company_country` now has an empty string as default when source field has no value
      - `country_url` now has an empty string as default when source field has no value

## API

  - `POST /v3/search/companieshousecompany`: All `sortby` options and filters were removed as these were not being used by any client.

## Database schema

  - **Investment** The columns `number_new_jobs_with_zero (int NULL)`, `number_safeguarded_jobs_with_zero (int NULL)` and `total_investment_with_zero (decimal NULL)` were added to `mi` database. These column contain the same values as their counterparts without `_with_zero` suffix except instead of NULL a zero should be given.
  - **Investment** The table `datahub.mi_dashboard_miinvestmentproject` has been renamed to `mi_dashboard_miinvestmentproject` as the dashboard software doesn't support dots in the table names.

# Data Hub API 8.4.1 (2018-12-20)

## Internal changes

  - The database connection configuration was updated to prevent unnecessary MI database transactions during API requests.

# Data Hub API 8.4.0 (2018-12-20)

## Deprecations and removals

  - **Companies** The column `company_company.alias` is deprecated and it will be deleted on or after January, 7. Please use `company_company.trading_names` instead.

  - **Companies** The endpont `/company/<uuid:pk>/core-team` was deleted, please use `/company/<uuid:pk>/one-list-group-core-team` instead.

  - **Companies** The field `trading_name` is deprecated from all GET company endpoints and GET/POST search endpoints and will be removed on or after January, 7. Please use the array field `trading_names` instead. However, `trading_name` is not deprecated when adding/editing a trading name using POST/PATCH as the new `trading_names` field is currently read-only.

  - **Interactions** `GET /v3/search`, `POST /v3/search/interaction`: the `net_company_receipt` field is deprecated for interaction search responses and will be removed on or after 27 December.
    
    `GET /v3/search`, `POST /v3/search/interaction`: the `grant_amount_offered` field is deprecated for interaction search responses and will be removed on or after 27 December.

## Features

  - **Companies** Companies now have a `trading names` field defined as a list of strings. It will eventually replace alias/trading\_name.
  - **Interactions** It's now possible to filter interactions by whether they contain policy feedback when searching for interactions.
  - **OMIS** The UK region and sector of an OMIS order can now be edited from the admin site.

## Bug fixes

  - **OMIS** Viewing OMIS order assignees (advisers in the market) now requires the `order.view_orderassignee` permission.
    
    Changing OMIS order assignees (advisers in the market) now requires the `order.change_orderassignee` permission.
    
    Viewing OMIS order subscribers (advisers in the UK) now requires the `order.view_ordersubscriber` permission.
    
    Changing OMIS order subscribers (advisers in the UK) now requires the `order.change_ordersubscriber` permission.

## Internal changes

  - **Interactions** Nightly MI dashboard pipeline was added. It loads the anonymised Investment Project data to a separate database that powers MI Dashboards.
  - **Interactions** The interaction Elasticsearch mapping was cleaned up substantially by replacing unnecessary nested fields with object fields and not indexing `is_event`. The removal of nested fields means each interaction is now represented by a single document, instead of 14 documents (as was the case previously).

## API

  - **Companies** The endpont `/company/<uuid:pk>/core-team` was deleted, please use `/company/<uuid:pk>/one-list-group-core-team` instead.

  - **Companies** `GET /v3/company` and `GET /v3/company/<uuid:pk>`: The read-only fields `number_of_employees` and `is_number_of_employees_estimated` were added and will only be set when `duns_number` is not empty.

  - **Companies** `GET /v3/company/<uuid:pk>` now returns the read-only field `trading_names` which replaces `trading_name`.

  - **Companies** `GET /v3/search` now also searches for a company's `trading_names` when using the `term` param.
    
    `POST /v3/search/company` now also returns and searches for a company's `trading_names` when using the `name` param.
    
    `GET /v3/search/company/autocomplete` now also returns and searches for a company's `trading_names`
    
    `POST /v3/search/contact` now also searches for a company's `trading_names` when using the `company_name` param.
    
    `POST /v3/search/interaction` now also searches for a company's `trading_names` when using the `company_name` param.
    
    `POST /v3/search/order` now also searches for a company's `trading_names` when using the `company_name` param.

  - **Companies** `GET /v3/company` and `GET /v3/company/<uuid:pk>`: The read-only fields `turnover` and `is_turnover_estimated` were added and will only be set when `duns_number` is not empty. The value of `turnover` is in USD.

  - **Interactions** `GET /v3/search`, `POST /v3/search/interaction`: the `net_company_receipt` field is deprecated for interaction search responses and will be removed on or after 27 December.
    
    `GET /v3/search`, `POST /v3/search/interaction`: the `grant_amount_offered` field is deprecated for interaction search responses and will be removed on or after 27 December.

  - **Interactions** `POST /v3/search/interaction`: A new boolean filter, `was_policy_feedback_provided`, was added.

  - **Investment** The field `likelihood_of_landing` is deprecated and has been removed from all investment projects APIs, please use `likelihood_to_land` instead.

  - **OMIS** `GET /v3/omis/order/<id>/assignee` now requires the `order.view_orderassignee` permission.
    
    `PATCH /v3/omis/order/<id>/assignee` now requires the `order.change_orderassignee` permission.
    
    `GET /v3/omis/order/<id>/subscriber-list` now requires the `order.view_ordersubscriber` permission.
    
    `PUT /v3/omis/order/<id>/subscriber-list` now requires the `order.change_ordersubscriber` permission.

## Database schema

  - **Companies** The column `company_company.alias` is deprecated and it will be deleted on or after January, 7. Please use `company_company.trading_names` instead.
  - **Companies** The columns `number_of_employees (int NULL)` and `is_number_of_employees_estimated (bool NULL)` were added to the table `company_company`. They should only be used as replacement for `employee_range` when the field `duns_number` is set.
  - **Companies** The column `company_company.trading_names` was added as nullable varchar\[\]. It will eventually replace `company_company.alias`.
  - **Companies** The columns `turnover (bigint NULL)` and `is_turnover_estimated (bool NULL)` were added to the table `company_company`. They should only be used as replacement for `turnover_range` when the field `duns_number` is set.

# Data Hub API 8.3.0 (2018-12-17)

## Deprecations and removals

  - **Interactions** `POST /v3/interaction`: omitting the `was_policy_feedback_provided` field is deprecated and it will become a mandatory field on or after 27 December 2018.
    
    `GET,POST /v3/interaction, GET,PATCH /v3/interaction/<id>`: the `policy_issue_type` field is deprecated and will become read-only on or after 27 December 2018, and removed on or after 7 January 2019.
    
    `GET,POST /v3/interaction, GET,PATCH /v3/interaction/<id>`: the value `policy_feedback` for the `kind` field is deprecated and will be not be accepted on or after 27 December 2018.
    
    `interaction_interaction`: the `policy_issue_type` column is deprecated and will be removed on or after 7 January 2019.
    
    `interaction_interaction`: the value `policy_feedback` for the `kind` column is deprecated and `was_policy_feedback_provided` should be used to identify policy feedback instead.

## Features

  - **Interactions** It's now possible to record policy feedback within a service delivery or standard interaction, with one or more policy issue types, one or more policy areas and free text policy feedback notes. This is intended to replace the existing policy feedback functionality (where policy feedback is a separate type of interaction).

## API

  - **Interactions** `GET,POST /v3/interaction, GET,PATCH /v3/interaction/<id>`: `was_policy_feedback_provided` was added as a boolean field.
    
    `GET,POST /v3/interaction, GET,PATCH /v3/interaction/<id>`: `policy_issue_types` was added as an array field.
    
    `GET,POST /v3/interaction, GET,PATCH /v3/interaction/<id>`: `policy_feedback_notes` was added as a text field.
    
    `POST /v3/interaction`: omitting the `was_policy_feedback_provided` field is deprecated and it will become a mandatory field on or after 27 December 2018.
    
    `GET,POST /v3/interaction, GET,PATCH /v3/interaction/<id>`: the `policy_issue_type` field is deprecated and will become read-only on or after 27 December 2018, and removed on or after 7 January 2019.
    
    `GET,POST /v3/interaction, GET,PATCH /v3/interaction/<id>`: the value `policy_feedback` for the `kind` field is deprecated and will be not be accepted on or after 27 December 2018.

## Database schema

  - **Interactions** `interaction_interaction`: `was_policy_feedback_provided` was added as a nullable boolean column.
    
    `interaction_interaction`: `policy_feedback_notes` was added as a nullable text column.
    
    `interaction_interaction_policy_issue_types` was added as a new many-to-many table linking `interaction_interaction` and `metadata_policyissuetype`.
    
    `interaction_interaction`: the `policy_issue_type` column is deprecated and will be removed on or after 7 January 2019.
    
    `interaction_interaction`: the value `policy_feedback` for the `kind` column is deprecated and `was_policy_feedback_provided` should be used to identify policy feedback instead.

# Data Hub API 8.2.0 (2018-12-13)

## Deprecations and removals

  - **Investment** The column `investment_investmentproject.likelihood_of_landing` is deprecated and will be deleted on or after December, 20. Please use `investment_investmentproject.likelihood_to_land` with a foreign key to `investment_likelihoodtoland` instead of an integer value.
    
    The field `likelihood_of_landing` is deprecated and will be removed from all investment projects APIs on or before December 20, please use `likelihood_to_land` instead.

## Features

  - **Companies** Company autocomplete support has been added to be utilised on search pages and forms when there is a need to add a company to another entity such as an investment project or interaction.
  - **Interactions** The notes field is now optional for standard interactions and for service deliveries.

## API

  - **Companies** New endpoint `GET /v3/search/company/autocomplete` which supports a query argument of `term` that will return the `id`, `name` and `trading_name` of any company matching the search query.

  - **Companies** `PATCH /v3/company/<uuid:pk>`: the following fields are now read-only if the company has a non-blank `duns_number` field:
    
      - name
      - trading\_name
      - company\_number
      - vat\_number
      - registered\_address\_1
      - registered\_address\_2
      - registered\_address\_town
      - registered\_address\_county
      - registered\_address\_postcode
      - registered\_address\_country
      - website
      - trading\_address\_1
      - trading\_address\_2
      - trading\_address\_town
      - trading\_address\_county
      - trading\_address\_postcode
      - trading\_address\_country
      - business\_type
      - employee\_range
      - turnover\_range
      - headquarter\_type
      - global\_headquarters

  - **Interactions** `GET,POST /v3/interaction`, `GET,PATCH /v3/interaction/<id>`: The notes field can now be left blank (as an empty string) for standard interactions and for service deliveries.

  - **Investment** The field `likelihood_of_landing` is deprecated and will be removed from all investment projects APIs on or before December 20, please use `likelihood_to_land` instead.

  - **Investment** `POST /v3/investment` endpoint now accepts `likelihood_to_land` as an optional property that can be set whilst creating an investment project. The property expects a `investment_likelihoodtoland` id.
    
    `GET /v3/investment/<uuid:pk>` endpoint now includes `likelihood_to_land` field in the response.
    
    `PATCH /v3/investment/<uuid:pk>` endpoint now accepts `likelihood_to_land` as an optional property that can be set whilst updating an investment project. The property expects a `metadata_likelihoodtoland` id.
    
    New endpoint `GET /metadata/likelihood-to-land/` added that returns all possible `likelihood_to_land` options.
    
    `POST /v3/search/investment_project/export` response body now includes `likelihood_to_land`.

## Database schema

  - **Companies** The field `company_company.duns_number` was made unique.
  - **Investment** Column `likelihood_to_land` has been added to `investment_investmentproject` table and is nullable.

# Data Hub API 8.1.0 (2018-12-10)

## Features

  - **Companies** Companies that have not been updated in the last ten years can now be deleted using the `delete_old_records` management command.
  - **Contacts** Contacts that have not been updated in the last ten years can now be deleted using the `delete_old_records` management command.

## Internal changes

  - Various dependencies were updated.

# Data Hub API 8.0.0 (2018-12-06)

## Deprecations and removals

  - **Companies** The field `classification` was removed from all company API endpoints.
  - **Companies** The column `company_company.classification_id` is deprecated and will be deleted on or after December 13. Please use `company_company.one_list_tier_id` with foreign keys to `company_onelisttier` instead of `metadata_companyclassification`. The IDs were preserved so the records in the `company_onelisttier` table match the records in the deprecated `metadata_companyclassification`.
  - **Companies** The field `one_list_account_owner` was removed from all company API endpoints, please use `one_list_group_global_account_manager` instead.
  - The API endpoint `/metadata/company-classification` was removed.
  - The table `metadata_companyclassification` is deprecated and will be deleted on or after December 13. Please use `company_onelisttier` instead.

## Features

  - **Companies** The field `Company.classification` was made read-only in the Django Admin and is now populated automatically from `Company.one_list_tier`.
  - **Investment** Investment projects that have not been updated in the last ten years can now be deleted using the `delete_old_records` management command.
  - **OMIS** OMIS orders that have not been updated in the last seven years can now be deleted using the `delete_old_records` management command.

## Internal changes

  - **Investment** It is now possible to delete investment projects using added management command `delete_investment_project`.
  - **Investment** It is now possible to unarchive and update status of investment projects using added management command `update_investment_project_archive_state`.

## API

  - **Companies** The field `classification` was removed from all company API endpoints.
  - **Companies** The field `one_list_account_owner` was removed from all company API endpoints, please use `one_list_group_global_account_manager` instead.
  - **Investment** The global account manager field in the `POST /v3/search/investment_project/export` response body now inherits the value from the investor company's Global Headquarters in case of subsidiaries.
  - The API endpoint `/metadata/company-classification` was removed.

## Database schema

  - **Companies** The column `company_company.classification_id` is deprecated, please check the *Deprecations* section for more details.
  - **Companies** Blank values in the `company_company.duns_number` field are now NULLs instead of empty strings.
  - **Companies** The column `company_company.one_list_tier_id` was added and replaces the column `company_company.classification_id`.
  - The table `metadata_companyclassification` is deprecated, please check the *Deprecations* section for more details.

# Data Hub API 7.11.0 (2018-11-29)

## Features

  - **Companies** Editing `CompanyClassification` using the Django Admin is temporaneously suspended to allow it to be migrated into the newly created `OneListTier`.
  - **Companies** The field `duns_number` representing the nine-digit D\&B unique identifier was added to the Company model and can be updated using the Django Admin.
  - **Investment** New read-only field `level_of_involvement_simplified` has been added that contains simplified information about the level of involvement. It has one of three values: `unspecified`, `not_involved` and `involved` derived from `level_of_involvement` field. This field can be filtered by using the search endpoint.
  - **Investment** `Involvements` section in Django admin is now view only as values for level of involvement are not meant to be changed.

## API

  - **Companies** `GET /v3/company/<uuid:pk>`, `GET /v3/company` and `POST /v3/search/company` now return the read-only field `duns_number` representing the nine-digit D\&B unique identifier.

  - **Investment** `GET /v3/investment/<uuid:pk>/` endpoint now includes `level_of_involvement_simplified` field in the response.
    
    `POST /v3/search/investment_project/`: new filter `level_of_involvement_simplified` was added.

## Database schema

  - **Companies** The column `company_company.duns_number` representing the nine-digit D\&B unique identifier was added.
  - **Companies** The table `company_onelisttier` was added with the intention of replacing `metadata_companyclassification` in the near future.

# Data Hub API 7.10.0 (2018-11-26)

## Deprecations and removals

  - **Companies** *(Correction)* The API field `one_list_account_owner` is deprecated and will be removed on or after November, 29. The recommended and most efficient way to upgrade is to use the field `one_list_group_global_account_manager` instead.

## Bug fixes

  - The `delete_old_records` and `delete_orphans` management commands were optimised to use less memory and be faster when run without the `--simulate` or `--only-print-queries` arguments.

## Internal changes

  - Various dependencies were updated.

## API

  - **Companies** *(Correction)* The API field `one_list_account_owner` is deprecated and will be removed on or after November, 29. The recommended and most efficient way to upgrade is to use the field `one_list_group_global_account_manager` instead.
  - **Companies** `GET /company/<uuid:pk>` and the other company endpoints now return the read-only field `one_list_group_global_account_manager` with details of the One List Global Account Manager for the group that the company is part of. This value is inherited from the Global Headquarters.

# Data Hub API 7.9.0 (2018-11-23)

## Database schema

  - **Companies** The table `company_companycoreteammember` was renamed to `company_onelistcoreteammember`.

# Data Hub API 7.8.0 (2018-11-22)

## Deprecations and removals

  - **Companies** The API field `classification` is deprecated and will be removed on or after November, 29. Please use <span class="title-ref">one\_list\_group\_tier</span> instead.
  - **Companies** The API field `one_list_account_owner` is deprecated and will be removed on or after November, 29. Please use `GET  /company/<uuid:pk>/one-list-group-core-team` and get the item in the list with `is_global_account_manager` = True instead.
  - **Companies** The endpoint `GET /company/<uuid:pk>/core-team` is deprecated and will be removed on or after November, 29. Please use `GET /company/<uuid:pk>/one-list-group-core-team` instead.
  - The API endpoint `/metadata/company-classification` is deprecated as not currently necessary. It will be completely removed on or after November, 29.

## Internal changes

  - **Investment** The permission `Can change SPI report (change_spireport)` was renamed to `Can view SPI report (view_spireport)` as Django 2.1 supports view permission and SPI report is read only.

## API

  - **Companies** The field `classification` is deprecated and will be removed on or after November, 29. Please use <span class="title-ref">one\_list\_group\_tier</span> instead.

  - **Companies** The field `one_list_account_owner` is deprecated and will be removed on or after November, 29. Please use `GET  /company/<uuid:pk>/one-list-group-core-team` and get the item in the list with `is_global_account_manager` = True instead.

  - **Companies** The One List Core Team endpoint was changed:
    
    `GET /company/<uuid:pk>/core-team` was renamed to `GET /company/<uuid:pk>/one-list-group-core-team`. The old `/core-team` endpoint still exists but will be completely removed on or after November, 29.
    
    `GET /company/<uuid:pk>/one-list-group-core-team` now returns the Core Team for the group that the company is part of. All companies in the group inherit that team from their Global Headquarters.

  - **Companies** `GET /v3/company/<uuid:pk>` and `GET /v3/company` now include the read-only field `one_list_group_tier` which is the One List Tier for the group, inherited from the Global Headquarters.

  - **Companies** The field <span class="title-ref">classification</span> is now read-only in all company endpoints.

  - **Investment** `POST /v3/investment/` endpoint now accepts `country_investment_originates_from` as an optional property that can be set whilst creating an investment project. The property expects an id of a country.
    
    `GET /v3/investment/<uuid:pk>/` endpoint now includes `country_investment_originates_from` field in the response.
    
    `PATCH /v3/investment/<uuid:pk>/` endpoint now accepts `country_investment_originates_from` as an optional property that can be set whilst updating an investment project. The property expects an id of a country.

  - The endpoint `/metadata/company-classification` is deprecated as not currently necessary. It will be completely removed on or after November, 29.

## Database schema

  - **Investment** Column `country_investment_originates_from` has been added to `investment_investmentproject` table and is nullable.

# Data Hub API 7.7.0 (2018-11-15)

## Features

  - **Investment** Exports of search results now include the town or city of the investor company.

## Internal changes

  - Countries now have defined ISO codes.
  - Django Rest Framework was updated to version 3.9.0.

## API

  - **Investment** `POST /v3/search/investment_project/export`: the field 'Investor company town or city' was added to the CSV output.

# Data Hub API 7.6.0 (2018-11-12)

## Features

  - **Companies** A tool for merging duplicate companies was added to the admin site. This tool moves contacts and interactions from one company to another, and archives the company that the contacts and interactions were moved from. The tool is accessed via a link displayed when viewing a single company (in the admin site). Some limitations exist (for example, companies with investment projects or OMIS orders cannot be merged into another company).

## Internal changes

  - Various dependencies were updated.

# Data Hub API 7.5.0 (2018-11-08)

## Deprecations and removals

  - **Advisers** The column `company_advisor.use_cdms_auth` was deleted from the database.

## Features

  - **Investment** First part of the streamlined investment flow. Feature flag `streamlined-investment-flow` introduced to control when the project manager information is required and to allow the assign pm stage to be deprecated.

## Internal changes

  - **Investment** A command `activate_streamlined_investment_flow` has been added to active the `streamlined_investment_flow` feature and update any project at the `Assign PM` stage to `Prospect`.
  - The `countries.yaml` fixture was updated to reflect the current production data.
  - It's not possible to change `Countries` and `OverseasRegions` from the django admin anymore. They will need to be updated using data migrations instead.
  - The Elasticsearch Python client libraries were updated to 6.x versions, as was the Docker image used during development.
  - A setting to sync updates to records to Elasticsearch using Celery (rather than the thread pool) was adding. This will improve performance when many records are updated at once, and increase reliability as failed synchronisation attempts are automatically retried. When the setting is enabled, Redis and Celery must be configured and running to use endpoints that create or update records.

## API

  - **Investment** `GET /metadata/investment-project-stage/<uuid:pk>/` endpoint no longer returns null values for field `exclude_from_investment_flow`. All existing records now return false with the exception of 'Assign PM' which returns true.

## Database schema

  - **Advisers** The column `company_advisor.use_cdms_auth` was deleted from the database.
  - **Investment** Column `exclude_from_investment_flow` on `metadata_investmentprojectstage` table is no longer nullable and the default value has been set to False. Existing entries have all been updated to False with the exception of 'Assign PM' which has been set to True.
  - A new field `iso_alpha2_code` was added to the `metadata_country` table. It has not been populated yet.

# Data Hub API 7.4.0 (2018-11-01)

## Features

  - **Companies** Company timeline now includes `data_source_label` field that contains human-readable data source description.
  - **Companies** New fields named `transferred_to` and `transfer_reason` have been added to indicate if a company has had its data transferred to another record and should no longer be used. The field contains a reference to the company that should be used instead. The field cannot be directly changed; it will be set by an upcoming admin tool for merging duplicate companies.
  - **Investment** A new field `exclude_from_investment_flow` has been added to the `InvestmentProjectStage` metadata to indicate if a stage should be excluded from the investment flow. The field will be used to aid with deprecating and adding new stages.

## Internal changes

  - Python was updated from version 3.6.6 to 3.6.7 in deployed environments.

## API

  - **Companies** `GET /v3/company/<uuid:pk>/timeline` endpoint now includes `data_source_label` field in the response. This field contains human-readable data source description.

  - **Companies** `GET,POST /v3/company`, `GET,POST /v3/company/<id>`: New, optional read-only fields named `transferred_to` and `transfer_reason` have been added to indicate if a company has had its data transferred to another record and should no longer be used. When set, this field contains two sub-fields (`id` and `name`) which give details of the company that should be used instead. The only possible value for transfer\_reason at present is `duplicate`, which indicates that it was a duplicate record.
    
    `GET,POST /v3/company/unarchive`: It is not possible to unarchive a company that has a value in the `transferred_to` field.

  - **Investment** `GET /metadata/investment-project-stage/<uuid:pk>/` endpoint now includes `exclude_from_investment_flow` field in the response.

## Database schema

  - **Companies** A new nullable column `transferred_to` has been added to the `company_company` table as a foreign key to another company record. The column indicates that data about the company has been transferred to another record, and the referenced company is the one that should be used instead.
    
    A new column `transfer_reason` has been added to the `company_company` table. This indicates the reason that data about the company was transferred. The current possible values are an empty string, or `'duplicate'`.

  - **Investment** A new column `exclude_from_investment_flow` has been added to the `metadata_investmentprojectstage` table. The column indicates if the stage should be excluded from the investment flow timeline.

# Data Hub API 7.3.0 (2018-10-25)

## Deprecations and removals

  - **Advisers** The field `use_cdms_auth` is deprecated and will be removed on or after 1 November.
  - The table `leads_businesslead` was deleted.

## Features

  - **Interactions** Policy feedback interactions are now always excluded from interaction exports (regardless of the current user's permissions).
  - **Investment** SPI report now shows "Project manager first assigned by" (who first time assigned a project manager) column.

## Internal changes

  - Various dependencies were updated.

## API

  - **Interactions** `POST /v3/search/interaction/export` now always excludes policy feedback interactions (regardless of the current user's permissions).

## Database schema

  - **Advisers** The column `company_advisor.use_cdms_auth` is deprecated and will be removed on or after 1 November.
  - **Investment** The column `investment_investmentproject.project_manager_first_assigned_by` has been added. It is nullable and contains a foreign key to the adviser who first time assigned a project manager.
  - The table `leads_businesslead` was deleted.

# Data Hub API 7.2.0 (2018-10-18)

## Deprecations and removals

  - All business leads endpoints were removed from the API.

## Features

  - **Investment** SPI report now shows "Enquiry type" (the type of interaction that triggered the end of SPI1) and "Enquiry processed by" (who has created the interaction) columns.
  - When viewing a record in the admin site, a link to the page for the record in the main application is now displayed (when applicable).

## Bug fixes

  - **Contacts** The speed of the admin site tool for loading marketing email opt-outs was improved via the creation of an additional database index.
  - **Investment** Estimated land date is now validated when other required fields are missing.

## API

  - The following endpoints were removed:
    
    GET,POST /v3/business-leads
    
    GET,PATCH /v3/business-leads/\<uuid:pk\>
    
    POST /v3/business-leads/\<uuid:pk\>/archive
    
    POST /v3/business-leads/\<uuid:pk\>/unarchive

# Data Hub API 7.1.0 (2018-10-11)

## Deprecations and removals

  - **Contacts** The column `company_contact.contactable_by_dit` has been deleted from the database.
    
    The column `company_contact.contactable_by_uk_dit_partners` has been deleted from the database.
    
    The column `company_contact.contactable_by_overseas_dit_partners` has been deleted from the database.
    
    The column `company_contact.contactable_by_email` has been deleted from the database.
    
    The column `company_contact.contactable_by_phone` has been deleted from the database.

  - `GET /whoami/` no longer returns the `read_*` permissions that were being returned for backwards compatibility following the introduction of `view_*` permissions.

## Internal changes

  - Various dependencies were updated.

## API

  - `GET /whoami/` no longer returns the `read_*` permissions that were being returned for backwards compatibility following the introduction of `view_*` permissions.

## Database schema

  - **Contacts** The column `company_contact.contactable_by_dit` has been deleted from the database.
    
    The column `company_contact.contactable_by_uk_dit_partners` has been deleted from the database.
    
    The column `company_contact.contactable_by_overseas_dit_partners` has been deleted from the database.
    
    The column `company_contact.contactable_by_email` has been deleted from the database.
    
    The column `company_contact.contactable_by_phone` has been deleted from the database.

# Data Hub API 7.0.0 (2018-10-04)

## Deprecations and removals

  - **Contacts** The field `contactable_by_dit` was removed from the API. The database column will be deleted with the next release.
    
    The field `contactable_by_uk_dit_partners` was removed from the API. The database column will be deleted with the next release.
    
    The field `contactable_by_overseas_dit_partners` was removed from the API. The database column will be deleted with the next release.
    
    The field `contactable_by_email` was removed from the API. The database column will be deleted with the next release.
    
    The field `contactable_by_phone` was removed from the API. The database column will be deleted with the next release.

  - Business leads table and endpoints are deprecated. Please check the API and Database schema categories for more details.

## Features

  - **Interactions** The character limit for the notes field was increased from 4000 to 10,000.

## Internal changes

  - The index.mapping.single\_type Elasticsearch setting is no longer set to improve compatibility with Elasticsearch 6.x.
  - Various dependencies were updated.

## API

  - **Contacts** The field `contactable_by_dit` was removed from all contact endpoints.
    
    The field `contactable_by_uk_dit_partners` was removed from all contact endpoints.
    
    The field `contactable_by_overseas_dit_partners` was removed from all contact endpoints.
    
    The field `contactable_by_email` was removed from all contact endpoints.
    
    The field `contactable_by_phone` was removed from all contact endpoints.

  - **Interactions** The character limit for the notes field was increased from 4000 to 10000 for the following endpoints:
    
    `GET,POST /v3/interaction`
    
    `GET,PATCH /v3/interaction/<uuid:pk>`

  - The following endpoints are deprecated and will be removed on or after October 11:
    
    `GET,POST /v3/business-leads`
    
    `GET,PATCH /v3/business-leads/<uuid:pk>`
    
    `POST /v3/business-leads/<uuid:pk>/archive`
    
    `POST /v3/business-leads/<uuid:pk>/unarchive`

## Database schema

  - **Contacts** The column `company_contact.contactable_by_dit` was made nullable in preparation for its removal.
    
    The column `company_contact.contactable_by_uk_dit_partners` was made nullable in preparation for its removal.
    
    The column `company_contact.contactable_by_overseas_dit_partners` was made nullable in preparation for its removal.
    
    The column `company_contact.contactable_by_email` was made nullable in preparation for its removal.
    
    The column `company_contact.contactable_by_phone` was made nullable in preparation for its removal.

  - The table `leads_businesslead` is deprecated and will be removed on or after October 11.

# Data Hub API 6.4.0 (2018-09-27)

## Deprecations and removals

  - **Companies** The column `company_company.account_manager_id` was deleted from the database.

## Features

  - **Contacts** A list of email addresses to opt out of marketing emails can now be loaded via the admin site.
  - URLs in CSV exports and reports are no longer clickable when the CSV file is opened in Excel. This is because the links do not behave correctly when clicked on in Excel (see <https://support.microsoft.com/kb/899927> for further information on why).

## Bug fixes

  - **Companies** The link in the admin site to export the One List was removed from the adviser, Companies House company, contact and export experience category lists. (It still appears on the company list as originally intended.)
  - **Investment** Restricted users can now list proposition documents associated to their team's investment projects.

## Internal changes

  - **Investment** Deletion of proposition or evidence document is now logged in UserEvent model. UserEvent records can be viewed from the admin site.
  - Various dependencies were updated.

## Database schema

  - **Companies** The column `company_company.account_manager_id` was deleted from the database.

# Data Hub API 6.3.0 (2018-09-12)

## Deprecations and removals

  - **Companies** The field <span class="title-ref">account\_manager</span> was removed from the API, from the Django admin and from the model definition. The database column will be deleted with the next release.

  - **Contacts** The field `contactable_by_dit` is deprecated. Please check the API and Database schema categories for more details.
    
    The field `contactable_by_uk_dit_partners` is deprecated. Please check the API and Database schema categories
    
    The field `contactable_by_overseas_dit_partners` is deprecated. Please check the API and Database schema categories for more details.
    
    The field `contactable_by_email` is deprecated. Please check the API and Database schema categories for more details.
    
    The field `contactable_by_phone` is deprecated. Please check the API and Database schema categories for more details.

## Features

  - **Companies** It's now possible to export company search results as a CSV file (up to a maximum of 5000 results).
  - **Contacts** It's now possible to export contact search results as a CSV file (up to a maximum of 5000 results).
  - **Investment** It is now possible to upload evidence documents for a given investment project.
  - **OMIS** It's now possible to export OMIS order search results as a CSV file (up to a maximum of 5000 results).
  - URLs in all CSV exports and reports were made clickable when the CSV file is opened in Excel. This was achieved by using the Excel HYPERLINK() function.
  - Existing read-only model views in the admin site were updated to disable the change button that previously had no purpose.
  - Performed exports of search results are now logged in a new model called UserEvent. UserEvent records can be viewed from the admin site.

## Bug fixes

  - **Investment** Proposition now needs to have at least one document uploaded in order to be completed. It is now optional to provide details when completing a proposition. This functionality is behind `proposition-documents` feature flag, that needs to be active in order for the new behaviour to work.

## API

  - **Companies** The field <span class="title-ref">account\_manager</span> was removed from all company endpoints.

  - **Companies** `POST /v3/search/company/export` was added for exporting company search results as a CSV file with up to 5000 rows. The `company.export_company` permission was also added and is required to use this endpoint.

  - **Contacts** `POST /v3/search/contact/export` was added for exporting contact search results as a CSV file with up to 5000 rows. The `company.export_contact` permission was also added and is required to use this endpoint.

  - **Contacts** `` `GET,POST /v3/contact ``<span class="title-ref"> and </span>`GET,POST /v3/contact/<uuid:pk>`\` the fields contactable\_by\_dit, contactable\_by\_uk\_dit\_partners, contactable\_by\_overseas\_dit\_partners, contactable\_by\_email, contactable\_by\_phone are deprecated and will be removed on or after September 11

  - **Investment** `GET /v3/investment/<investment project pk>/evidence` gets list of evidence documents.
    
    `POST /v3/investment/<investment project pk>/evidence` creates new evidence document upload.
    
    `GET /v3/investment/<investment project pk>/evidence/<evidence document pk>` gets details of evidence document
    
    `DELETE /v3/investment/<investment project pk>/evidence/<evidence document pk>` deletes given evidence document.
    
    `POST /v3/investment/<investment project pk>/evidence/<evidence document pk>/upload_callback` notifies that file upload has been completed and initiates virus scanning.
    
    `GET /v3/investment/<investment project pk>/evidence/<evidence document pk>/download` returns a signed URL to the document file object.
    
    Following permissions are required to use the endpoints:
    
    `evidence.add_all_evidencedocument`
    
    `evidence.view_all_evidencedocument`
    
    `evidence.change_all_evidencedocument`
    
    `evidence.delete_all_evidencedocument`
    
    For DA and LEP:
    
    `evidence.add_associated_evidencedocument`
    
    `evidence.view_associated_evidencedocument`
    
    `evidence.change_associated_evidencedocument`
    
    `evidence.delete_associated_evidencedocument`

  - **OMIS** `POST /v3/search/order/export` was added for exporting OMIS order search results as a CSV file with up to 5000 rows. The `order.export_order` permission was also added and is required to use this endpoint.

## Database schema

  - **Contacts** The column `` `contact.contactable_by_dit ``\` is deprecated and may be removed on or after 11 September.
    
    The column `` `contact.contactable_by_uk_dit_partners ``\` is deprecated and may be removed on or after 11 September.
    
    The column `` `contact.contactable_by_overseas_dit_partners ``\` is deprecated and may be removed on or after 11 September.
    
    The column `` `contact.contactable_by_email ``\` is deprecated and may be removed on or after 11 September.
    
    The column `` `contact.contactable_by_phone ``\` is deprecated and may be removed on or after 11 September.

  - **Investment** New tables `evidence_evidencedocuments`, `evidence_evidence_tag` and `evidence_evidencedocument_tags` have been added to enable evidence document upload.

  - **Investment** The `details` field in `proposition_proposition` table can now be blank.

  - **Investment** The `add_associated_investmentproject_proposition` permission has been renamed to `add_associated_proposition` to be consistent with other entities.

  - **Investment** The `change_associated_investmentproject_proposition` permission has been renamed to `change_associated_proposition` to be consistent with other entities.

  - **Investment** The `view_associated_investmentproject_proposition` permission has been renamed to `view_associated_proposition` to be consistent with other entities.

  - **Investment** The `delete_propositiondocument` permission has been renamed to `delete_all_propositiondocument` to be consistent with other entities.

  - **Investment** The `deleted_associated_propositiondocument` permission has been renamed to `delete_associated_propositiondocument`.

# Data Hub API 6.2.0 (2018-08-23)

## Deprecations and removals

  - **Companies** The field `account_manager` has been deprecated. Please check the API and Database schema categories for more details.
  - **Companies** The column `company_company.parent_id` has been deleted from the database.
  - `GET /whoami/` endpoint: `read_*` permissions have been renamed to `view_*`. This endpoint will return both `view_*` and `read_*` permissions for now but `read_*` permissions are deprecated and will soon be removed.

## Features

  - **Companies** It's now possible to export the one list via the django admin from the company changelist.
  - **Interactions** The CSV export of search results has been amended to return various additional columns.
  - **Investment** It's now possible to export investment project search results as a CSV file (up to a maximum of 5000 results).
  - The format of timestamps in CSV exports and reports was changed to YYYY-MM-DD HH-MM-SS for better compatibility with Microsoft Excel.
  - Document upload now uses V2 API of AV service.

## Bug fixes

  - Document upload streaming to AV service now uses a StreamWrapper to encode the file as multipart/form-data in order to send it to AV service. This fixes the problem when the file has been sent incorrectly.

## Internal changes

  - Django was updated to version 2.1.

## API

  - **Companies** `GET,POST /v3/company/<uuid:pk>` and `GET /v3/search/company`: the field `account_manager` has been deprecated and will be removed on or after August 30. Please use `one_list_account_owner` instead.
  - **Interactions** `GET /v3/interaction` can now be sorted by `dit_adviser__first_name`, `dit_adviser__last_name`, and `subject`.
  - **Investment** `POST /v3/search/investment_project/export` was added for exporting investment project search results as a CSV file with up to 5000 rows. The `investment.export_investmentproject` permission was also added and is required to use this endpoint.
  - `GET /whoami/` endpoint: `read_*` permissions have been renamed to `view_*`. This endpoint will return both `view_*` and `read_*` permissions for now but `read_*` permissions are deprecated and will soon be removed.

## Database schema

  - **Companies** The column `company_company.account_manager_id` has been deprecated and will be removed on or after August 30. Please use `company_company.one_list_account_owner_id` instead.
  - **Companies** The column `company_company.parent_id` has been deleted from the database.

# Data Hub 6.1.0 (2018-08-15)

## Investment projects

  - Added models for evidence documents (endpoints to follow in a future release)
  - Fixed a bug in the Celery task for SPI report creation that caused the task to fail. (As a result, S3 keys for future reports will no longer include the bucket name.)

## Search

  - Rewrote the mechanism for exporting results to run the search against Elasticsearch but extract data from PostgreSQL, and limited the number of rows exported to 5000
  - Removed all data exports expect for the interactions one (further changes to follow in a future release)

# Data Hub 6.0.0 (2018-08-14)

## Companies

  - Removed unused `parent` field from the model definition. The database column will be deleted from the schema on or after August 21

## Contacts

  - Added a management command to update the email marketing status of contacts using a CSV file

## Investment projects

  - Added the ability to upload documents to propositions
  - Removed old document functionality

## Internal changes

  - Stopped using nested Elasticsearch queries
  - Removed the migration path from legacy Elasticsearch single-index set-ups
  - Updated various dependencies
  - Updated the test data

# Data Hub 5.1.0 (2018-08-02)

## Companies

  - Added a core team member model to hold the advisers in the core team for a company
  - Updated the core team endpoint to return advisers from the core team member model
  - Improved the layout of the admin page for a company

## Miscellaneous

  - Updated the admin site to display the created on and by and modified on and by fields more consistently, and to correctly update those fields when changes are made via the admin site

## Internal changes

  - Removed (unused) Elasticsearch alias-related management commands
  - Improved timeout handling during Elasticsearch queries
  - Updated various dependencies

# Data Hub 5.0.0 (2018-07-31)

## Companies

  - Added a company core team endpoint at `/v3/company/<company-pk>/core-team` (currently only returning the global account manager)

## Internal changes

  - Moved to one Elasticsearch index per mapping type, and added a command (`./manage.py migrate_es`) to migrate Elasticsearch index mappings. See [docs/Elasticsearch migrations.md](https://github.com/uktrade/data-hub-api/blob/master/docs/Elasticsearch%20migrations.md) for more detail. (After upgrading, `./manage.py init_es` must be run to update index aliases.)
  - Fixed a random failure in the `TestListCompanies.test_sort_by_name` test
  - Added a contact for an archived company to the test data
  - Updated various dependencies

# Data Hub \< 5.0.0

Please check the [previous releases on GitHub](https://github.com/uktrade/data-hub-api/releases).
