`contacts` field was added to `GET /v4/pipeline-item/` and `PATCH /v4/pipeline-item/<UUID>` as an array field to replace the existing `contact` field.

The `contact` and `contacts` field will mirror each other (except that `contact` will only return a single contact).
