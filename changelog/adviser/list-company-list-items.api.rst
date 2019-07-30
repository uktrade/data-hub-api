The following endpoint was added:

``GET /v4/user/company-list``

It lists all the companies on the authenticated user's personal list, with responses in the following format::

    {
        "count": <int>,
        "previous": <url>,
        "next": <url>,
        "results": [
            {
                "company": {
                    "id": <string>,
                    "archived": <boolean>,
                    "name": <string>,
                    "trading_names": [<string>, <string>, ...]
                },
                "created_on": <ISO timestamp>,
                "latest_interaction": {
                    "id": <string>,
                    "created_on": <ISO timestamp>,
                    "date": <ISO date>,
                    "subject": <string>
                }
            },
            ...
        ]
    }        


``latest_interaction`` may be ``null`` if the company has no interactions.

Results are sorted by ``latest_interaction.date`` in reverse chronological order, with ``null`` values last.

The endpoint has pagination in line with other endpoints; to retrieve all results pass a large value for the ``limit`` query parameter (e.g. ``?limit=1000``).
