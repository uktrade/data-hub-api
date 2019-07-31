# DNB Search and Save API Contracts

## DNB Company Search (with DH hydration)

`POST /v4/dnb/company-search`

**Request JSON Body:**
- `search_term` - required - The string search term to use to find the company e.g. `"siemens"`
- `address_country` - optional - A string ISO Alpha 2 code representing the country to use to filter search results e.g. `"GB"`
- `address_postcode` - optional - A string representing the postcode of the business address/registered address to filter search results e.g. `"BN1 4SE"`
- `page_size` - optional - Integer number of results to show per page of results, defaults to `10`
- `page_number` - optional - Integer of the page of results to return, defaults to `1`

**Response:**

```
{
  "total_matches": 271,
  "total_returned": 2,
  "page_size": 2,
  "page_number": 1,
  "results": [
    {
      "dnb_company": {
        "duns_number": "12345678",
        "primary_name": "Some company name",
        "trading_names": [
          "Some trading name"
        ],
        "registration_numbers": [
          {
            "registration_type": "uk_companies_house_number",
            "registration_number": "1234567"
          }
        ],
        "global_ultimate_duns_number": "123456789",
        "global_ultimate_primary_name": "Some parent company name",
        "domain": "example.co.uk",
        "is_out_of_business": false,
        "address_line_1": "123 Fake Street",
        "address_line_2": "",
        "address_town": "Brighton",
        "address_county": "",
        "address_postcode": "BN1 4SE",
        "address_country": "GB",
        "registered_address_line_1": "",
        "registered_address_line_2": "",
        "registered_address_town": "Brighton",
        "registered_address_county": "",
        "registered_address_postcode": "BN1 4SE",
        "registered_address_country": "GB",
        "annual_sales": 1860000000,
        "annual_sales_currency": "USD",
        "is_annual_sales_estimated": null,
        "employee_number": 2000,
        "is_employees_number_estimated": true,
        "industry_codes": [
          {
            "usSicV4": "1623",
            "usSicV4Description": "Water/sewer/utility construction"
          }
        ],
        "legal_status": "corporation"
      },
      "datahub_company": {
        "id": "0fb3379c-341c-4da4-b825-bf8d47b26baa",
        "latest_interaction": {
          "id": "ec4a46ef-6e50-4a5c-bba0-e311f0471312",
          "created_on": "2019-08-01T18:10:00",
          "date": "2019-08-01",
          "subject": "Meeting between DIT and Joe Bloggs"
        }
      }
    },
    {
      "dnb_company":
        "duns_number": "219999999",
        "primary_name": "Some other company",
        "trading_names": [],
        "registration_numbers": [
          {
            "registration_type": "uk_companies_house_number",
            "registration_number": "00016033"
          }
        ],
        "global_ultimate_duns_number": "319999999",
        "global_ultimate_primary_name": "Some other company parent",
        "domain": "example.co.uk",
        "is_out_of_business": false,
        "address_line_1": "123 ABC Road",
        "address_line_2": "",
        "address_town": "Brighton",
        "address_county": "",
        "address_postcode": "BN2 9QB",
        "address_country": "GB",
        "registered_address_line_1": "",
        "registered_address_line_2": "",
        "registered_address_town": "Brighton",
        "registered_address_county": "",
        "registered_address_postcode": "BN2 9QB",
        "registered_address_country": "GB",
        "annual_sales": 1999999999,
        "annual_sales_currency": "USD",
        "is_annual_sales_estimated": null,
        "employee_number": 300,
        "is_employees_number_estimated": true,
        "industry_codes": [
          {
            "usSicV4": "3799",
            "usSicV4Description": "Mfg transportation equipment"
          }
        ],
        "legal_status": "corporation"
      },
      "datahub_company": null
    }
  ]
}
```

**Note:** All responses will have a `"dnb_company"` but depending on whether we
already have the company in Data Hub (and if it can be matched using the DUNS 
number) they may have an empty `"datahub_company"` value.

## Saving a DNB Company to Data Hub

### Approach 1 - Frontend responsibility

A very simple approach here (from backend's perspective) would be to shift the 
responsibility for saving a new company from DNB search results to the frontend.
This would mean that at the search stage, the frontend would need to cache the 
full search results temporarily - so that when a user selects a company that is 
not currently in Data Hub, it can be created calling the normal company creation 
API endpoint.

### Approach 2 - A new API endpoint

`POST /v4/dnb/save-company`

**Request JSON Body:**

- `duns_number` - required - DUNS number string, sourced from DNB search results.
 
**Response:**
This will respond with a standard serialized Data Hub company.  Under the hood 
it will most likely call through to a DNB API to get the company details and 
save it as a Data Hub company.

```
{
    "id": "346f78a5-1d23-4213-b4c2-bf48246a13c3",
    "name": "Archived Ltd",
    "trading_names": [],
    "uk_based": false,
    "company_number": null,
    "vat_number": "",
    "duns_number": "1234567",
    "created_on": "2014-11-11T09:00:00Z",
    "modified_on": "2017-07-16T10:00:00Z",
    "archived": false,
    "archived_documents_url_path": "",
    "archived_on": "2018-07-06T10:44:56Z",
    "archived_reason": "Company is dissolved",
    "archived_by": {
        "name": "John Rogers",
        "first_name": "John",
        "last_name": "Rogers",
        "id": "7bad8082-4978-4fe8-a018-740257f01637"
    },
    "description": "",
    "transferred_by": null,
    "transferred_on": null,
    "transferred_to": null,
    "transfer_reason": "",
    "website": null,
    "business_type": {
        "name": "Company",
        "id": "98d14e94-5d95-e211-a939-e4115bead28a"
    },
    "one_list_group_tier": null,
    "contacts": [],
    "employee_range": null,
    "number_of_employees": null,
    "is_number_of_employees_estimated": null,
    "export_to_countries": [],
    "future_interest_countries": [],
    "headquarter_type": null,
    "one_list_group_global_account_manager": null,
    "global_headquarters": null,
    "sector": null,
    "turnover_range": null,
    "turnover": 12345,
    "is_turnover_estimated": false,
    "uk_region": null,
    "export_experience_category": null,
    "address": {
        "line_1": "16 Getabergsvagen",
        "line_2": "",
        "town": "Geta",
        "county": "",
        "postcode": "22340",
        "country": {
            "name": "Malta",
            "id": "0850bdb8-5d95-e211-a939-e4115bead28a"
        }
    },
    "registered_address": {
        "line_1": "16 Getabergsvagen",
        "line_2": "",
        "town": "Geta",
        "county": "",
        "postcode": "22340",
        "country": {
            "name": "Malta",
            "id": "0850bdb8-5d95-e211-a939-e4115bead28a"
        }
    }
}

```
