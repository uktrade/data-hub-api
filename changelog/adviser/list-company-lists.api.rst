The following endpoint was added:

- ``GET /v4/company-list``: Lists the authenticated user's company lists.

  This is a paginated endpoint. Items are sorted by name, and are in the following format::

    {
      "id": "string",
      "name": "string",
      "created_on": "ISO timestamp"
    }
