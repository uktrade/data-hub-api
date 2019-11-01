A helper function for the "Update from DNB" admin feature was refactored as
a utility function `datahub.dnb_api.utils.update_company_from_dnb`.  The function
can optionally take an iterable of fields to update so that we can partially
update companies from DNB.
