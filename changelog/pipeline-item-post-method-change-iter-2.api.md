For existing endpoint `/v4/pipeline-item`, add additional 5 fields that can be seen below. All of these fields are optional and nullable at this stage so no additional validation required. The api should be able to create a pipeline item with or without any of these fields.

- `"contact_id" uuid NULL`
- `"sector_id" uuid NULL`
- `"potential_value" biginteger NULL`
- `"likelihood_to_win" int NULL`
- `"expected_win_date" timestamp with time zone NULL`
