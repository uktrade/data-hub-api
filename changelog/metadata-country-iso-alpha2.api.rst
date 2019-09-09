A field ``iso_alpha2_code`` was added to the ``GET /metadata/country/`` API
endpoint.

This endpoint now returns results of the following format:

```
...
{
    "id": "80756b9a-5d95-e211-a939-e4115bead28a",
    "name": "United Kingdom",
    "disabled_on": null,
    "overseas_region": null,
    "iso_alpha2_code": "GB"
},
{
    "id": "81756b9a-5d95-e211-a939-e4115bead28a",
    "name": "United States",
    "disabled_on": null,
    "overseas_region": {
        "name": "North America",
        "id": "fdfbbc8d-0e8a-479a-b10f-4979d582ff87"
    },
    "iso_alpha2_code": "US"
},
...
```
