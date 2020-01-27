A utility function `datahub.dnb_api.match.link_company_with_dnb` was added which
provides a mechanism for linking a Data Hub company record with a D&B company
record. The utility function saves the pertinent D&B data to the Data Hub record.

This will allow us to firstly provide an admin mechanism for quickly linking
companies, followed by an API endpoint.
