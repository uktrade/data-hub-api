A new table `company_companyexportcountry` was created.
It has foreign key fields `company_id` and `country_id`,
a `sources` ArrayField indicating whether it is user-entered or
from an externally-sourced (or both). The standard provenance fields
`created_on`, `created_by`, `modified_on`, `modified_by`, and the standard soft-delete field `disabled_on` are included. Additionally,
`disabled_by` indicates the user that disabled the export country, or
NULL if it was disabled by a non-user backend process.