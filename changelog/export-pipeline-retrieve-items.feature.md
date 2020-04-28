A new endpoint, `/v4/company-list/pipelineitem-collection`, was added to expose all export pipeline items for a given user. There is also the possibility of filtering the result by status. The following structure will be returned when a call is made to this endpoint:

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
