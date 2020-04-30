A new endpoint `/v4/pipeline-item`, was added to expose all pipeline items for a given user. Filterable fields are: `status` and order by fields are: `created_on` (desc). The following structure will be returned when a call is made to this endpoint:

 ```json
 ...
    [
        {
            "company": {
                "id": 123,
                "name": "Name",
                "turnover": 123,
                "export_potential": "Low",
            },
            "status": "win",
            "created_on": date,
        },
        ...
    ]
  ```
