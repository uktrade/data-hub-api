``GET /v3/interaction, GET /v3/interaction/<id>, POST /v3/interaction, PATCH /v3/interaction/<id>``:

``dit_participants`` was added to responses. This is an array in the following format::

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
