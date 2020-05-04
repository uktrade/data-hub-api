A new endpoint `/v4/pipeline-item/uuid`, was added to allow the frontend to `GET` or `PATCH` a pipeline item by uuid. Logic has been added to ensure that only the status can be patched. A 400 will be thrown if any field other than status is sent in the `PATCH` request. The below is the response returned from the `GET`. 


 ```json
 ...
    {
        "company": {
            "id": 123,
            "name": "Name",
            "turnover": 123,
            "export_potential": "Low",
        },
        "status": "win",
        "created_on": date,
    }
  ```