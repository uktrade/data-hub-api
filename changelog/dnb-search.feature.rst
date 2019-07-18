An initial endpoint was added for searching for companies through dnb-service
(https://github.com/uktrade/dnb-service/).  This endpoint takes care of auth
and proxies requests through to the service - it will return error responses
from the proxied DNB service.

There is further work to be done here in terms of iterating features and 
hardening the implementation.
