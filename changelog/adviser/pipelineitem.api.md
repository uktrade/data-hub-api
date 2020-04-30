`POST /v4/pipeline-item`

Expects a POST with JSON:

```
{
     'company': '<company.pk>',
     'status': '<pipeline_status>'
}
```

and returns 201 with following response upon success:

```
{
    {
        'id': '<company.pk>',
        'name': '<company.name>',
        'export_potential': '<company.export_potential>',
        'turnover': '<company.turnover>'
    },
    'status': '<pipeline_status>',
    'created_on': '<created datetime>'
}
```

It can raise:

- 401 for unauthenticated request
- 403 if the user doesn't have enough permissions
- 400 if the company is archived, company already exists for the user, company doesn't exist or status is not one of the predefined.
