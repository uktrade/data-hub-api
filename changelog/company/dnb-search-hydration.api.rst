``POST /v4/dnb/company-search``: This endpoint was modified to ensure that DNB
results were hydrated with the corresponding Data Hub company, if it is present
and can be matched (by duns number).

The API response returns Data Hub companies alongside DNB data in the following format::

    "datahub_company": {
        "id": "0f5216e0-849f-11e6-ae22-56b6b6499611",
        "latest_interaction": {
            "id": "e8c3534f-4f60-4c93-9880-09c22e4fc011",
            "created_on": "2018-04-08T14:00:00Z",
            "date": "2018-06-06",
            "subject": "Exported to Canada"
        }
    }

