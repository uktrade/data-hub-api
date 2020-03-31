A new API endpoint `POST /v4/dnb/company-investigation` was added which will eventually
replace `/v4/dnb/company-create-investigation` for creating new company record investigations
with D&B.  Right now the endpoint does some rudimentary validation of input, but otherwise 
responds with 501 NOT IMPLEMENTED.
The endpoint will be further fleshed out in subsequent work.
