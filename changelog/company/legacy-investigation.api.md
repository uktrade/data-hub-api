The endpoint `POST /v4/dnb/company-create-investigation` is deprecated and will be removed on or after 15 June.

It is replaced by `POST /v4/company/` which creates a stub Company record with `pending_dnb_investigation=True` and `POST /v4/dnb/company_investigation/` which creates a new investigation in `dnb-service`.
