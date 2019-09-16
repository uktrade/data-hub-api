The ``POST /v4/dnb/company-create`` endpoint was modified to return the boolean
``pending_dnb_investigation`` in responses representing created Data Hub 
companies.  

The format of the response is as follows::

  ...
  "pending_dnb_investigation": true,
  ...

