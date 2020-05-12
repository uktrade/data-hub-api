`GET /v4/company/<uuid:pk>/export-win` API endpoint is now updated to to allow export wins of merged companies to be surfaced on export tab for the target company.

`match_id` of the target company as well as all `transferred_from` companies are extracted from company matching service before supplying them to export wins service. Export wins service will in turn expose all wins matching those match ids.
