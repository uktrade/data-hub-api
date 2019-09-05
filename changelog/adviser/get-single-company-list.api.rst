The following endpoint was added:

- ``GET /v4/company-list/<id>``: Gets details of a single company list belonging to the authenticated user.

Responses are in the following format::

  {
    "id": "string",
    "name": "string",
    "item_count": integer,
    "created_on": "ISO timestamp"
  }
