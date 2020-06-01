The create company endpoint `POST /v4/company` was re-instated. This allows clients to create
stub Company records - i.e. Company records that are not matched with D&B records.
Companies created with this endpoint are created with `pending_dnb_investigation=True`.

The endpoint should be called with a POST body of the following format:
```
{
    'business_type': <uuid>,
    'name': 'Test Company',
    'address': {
        'line_1': 'Foo',
        'line_2': 'Bar',
        'town': 'Baz',
        'county': 'Qux',
        'country': {
            'id': <uuid>,
        },
        'postcode': 'AB5 XY2',
    },
    'sector': <uuid>,
    'uk_region': <uuid>,
}
```
