A new `PATCH /v4/company/<company-id>/update-one-list-core-team` endpoint to update the Core Team of One List company 
has been added. Adviser with correct permissions can update Core Team of a company.

Example request body:

```
{
  "core_team_members": [
    {
      "adviser": <adviser_1_uuid>
    },
    {
      "adviser": <adviser_2_uuid>
    }, 
    ...
  ]
}
```

Successful request should expect empty response with 204 (no content) HTTP status.
