This adds a management command, `delete_old_export_country_history`, to delete `CompanyExportCountryHistory` older than a specified date.

This is a temporary command to delete inaccurate `CompanyExportCountryHistory` objects
that were accidentally created during the data migration from the previous `Company.export_to_countries` and `Company.future_interest_countries` fields.
