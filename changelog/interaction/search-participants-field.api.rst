``GET /v3/search``, ``POST /v3/search/interaction``:

``dit_participants`` was added to interaction search results in responses. This is an array in the following format::

    [
        {
           "adviser": {
               "id": ...,
               "first_name": ...,
               "last_name": ...,
               "name": ...
           },
           "team": {
               "id": ...,
               "name": ...
           }
        },
        {
           "adviser": {
               "id": ...,
               "first_name": ...,
               "last_name": ...,
               "name": ...
           },
           "team": {
               "id": ...,
               "name": ...
           }
        },
        ...
    ]

This field is intended to replace the ``dit_adviser`` and ``dit_team`` fields.
