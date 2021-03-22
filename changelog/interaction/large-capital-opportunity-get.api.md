`GET /v3/interaction`, `GET /v3/interaction/<id>`: A `large_capital_opportunity` field was added to responses. 
If large capital opportunity interaction has been created, the field will have following structure:

  ```json
  {
    ...
    "large_capital_opportunity": {
      "id": <large_capital_opportunity_id>,
      "name": "Name of the opportunity",
    }
  }
  ```

  Otherwise, the value will be `null`.

