The following endpoint was added to the Data Hub API for submitting change requests to D&B:

- POST `/dnb/company-change-request/`

The endpoint requires a json payload with a valid `duns_number` for a company that exists in Data Hub and requested `changes` like so:

```
{
    'duns_number': '123456789',
    'changes': {
        'website': 'example.com',
    },
},
```
