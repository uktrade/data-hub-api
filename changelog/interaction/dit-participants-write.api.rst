``POST /v3/interaction, PATCH /v3/interaction/<id>``:

``dit_participants`` is now a valid field in request bodies. This should be an array in the following format::

    [
        {
           "adviser": {
               "id": ...
           }
        },
        {
           "adviser": {
               "id": ...
           }
        },
        ...
    ]

Note that the team for each participant will be set automatically. (If a team is provided it will be ignored.)

``dit_participants`` is intended to replace the ``dit_adviser`` and ``dit_team`` fields.
