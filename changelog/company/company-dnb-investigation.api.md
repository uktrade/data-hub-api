A new API endpoint was added for creating a DNB investigation; 
`POST /v4/dnb/company-investigation` takes company details and proxies 
them through to dnb-service e.g.

```shell
curl -X POST https://datahub.api/v4/dnb/company-investigation -d '{
  "company": "0fb3379c-341c-4da4-b825-bf8d47b26baa", # Data Hub company ID
  "name": "Joe Bloggs LTD",
  "website": "http://example.com", 
  "telephone_number": "123456789",
  "address": { 
     "line_1": "23 Code Street",
     "line_2": "Someplace",
     "town": "London",
     "county": "Greater London",
     "postcode": "W1 0TN",
     "country": "80756b9a-5d95-e211-a939-e4115bead28a",
  }
}'
```

Responds with:

```json
{
    "id": "11111111-2222-3333-4444-555555555555",
    "status": "pending",
    "created_on": "2020-01-05T11:00:00",
    "company_details": {
        "primary_name": "Joe Bloggs LTD",
        "domain": "example.com", 
        "telephone_number": "123456789",
        "address_line_1": "23 Code Street",
        "address_line_2": "Someplace",
        "address_town": "London",
        "address_county": "Greater London",
        "address_postcode": "W1 0TN",
        "address_country": "GB",
    }
}
```
