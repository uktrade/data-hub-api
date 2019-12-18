Interactions API `/v3/interaction`, `export_countries` tagged to an interaction are consolidated into `CompanyExportCountry` model, in order to maintain company export countries list. If a country added to an interaction doesn't already exist in company export countries, it will be added. If in case that country already exists, following business rules apply:

* `Status` of `InteractionExportCountry` added to an interaction with current date overrides the entry within `CompanyExportCountry` with older date.
* Whereas `Status` of `InteractionExportCountry` added to an interaction with past date can't override the entry within `CompanyExportCountry` with newer date.
* An interaction added with future date, will be treated as current date and existing rules apply.
