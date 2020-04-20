The following OMIS public endpoints have been deprecated and will be removed on or after 23rd April 2020:

    GET /v3/omis/public/order/<public-token>
    GET /v3/omis/public/order/<public-token>/invoice
    POST /v3/omis/public/order/<public-token>/payment-gateway-session
    GET /v3/omis/public/order/<public-token>/payment-gateway-session/<session-id>
    POST /v3/omis/public/order/<public-token>/payment
    GET /v3/omis/public/order/<public-token>/quote
    POST /v3/omis/public/order/<public-token>/quote/accept

Those endpoints have been replaced by their Hawk authenticated counterparts.
