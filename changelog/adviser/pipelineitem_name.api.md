# /v4/pipeline-item

New field `name` is now exposed in the result of `GET /v4/pipeline-item`.

`POST /v4/pipeline-item` will now take `name` field along with other fields when creating a new pipeline item. Validation error will not be raised when an entry already exists with that company for the user.
