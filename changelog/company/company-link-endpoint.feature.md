The following endpoint was added to Data Hub API:

- POST `/v4/dnb/company-link` {'company_id': <company_id>, 'duns_number': <duns_number>}

This endpoint would link a Data Hub company to a D&B record given a valid Data Hub company ID and a `duns_number`.
