`GET /v4/company-list/<pk>/item`: The latest interaction of each list item now includes an array of DIT participants in the `dit_participants` field. In context, the field has the following structure:

```json
{
    "results": [
        {
            "latest_interaction": {
                "dit_participants": [
                    {
                       "adviser": {
                           "id": ...,
                           "name": ...
                       },
                       "team": {
                           "id": ...,
                           "name": ...
                       }
                    },
                    ...
                ]
            }
        }
    ]
}
```
