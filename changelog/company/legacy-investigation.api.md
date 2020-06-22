The endpoint `POST /v4/dnb/company-create-investigation` has been removed from the `data-hub-api`.

It is replaced by `POST /v4/company/` which creates a stub Company record with `pending_dnb_investigation=True` and `POST /v4/dnb/company_investigation/` which creates a new investigation in `dnb-service`.
