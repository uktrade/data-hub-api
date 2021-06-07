A new `companies` field has been added to Interaction API. The field is being mirrored with the existing `company` field.
Both `company` and `companies` cannot be set at the same time.
If multiple companies are provided, the first one will be copied to `company` field. Refer to the API documentation for the schema.