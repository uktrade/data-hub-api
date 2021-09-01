Summary counts for each project stage can now be requested from the investment search endpoint.

```
POST /v3/search/investment_project
{
    "show_summary": true,
    ...filters
}

=>

{
    "count": 4,
    "results": ...,
    "summary": {
        "prospect": {
            "label": "Prospect",
            "id": <uuid>,
            "value": 3
        },
        "assign_pm": {
            "label": "Assign PM",
            "id": <uuid>,
            "value": 0
        },
        "active": {
            "label": "Active",
            "id": <uuid>,
            "value": 1
        },
        "verify_win": {
            "label": "Verify Win",
            "id": <uuid>,
            "value": 0
        },
        "won": {
            "label": "Won",
            "id": <uuid>,
            "value": 0
        }
    }
}
```
