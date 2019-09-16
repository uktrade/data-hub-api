The ``GET /v4/company`` and ``GET /v4/company/<uuid:pk>`` endpoints were 
modified to return the boolean ``pending_dnb_investigation`` in responses.  
The format of the responses are as follows::

  ...
  "pending_dnb_investigation": true,
  ...
