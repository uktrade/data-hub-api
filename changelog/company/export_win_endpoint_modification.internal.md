The company endpoint `company/<uuid:pk>/export-win` now returns an empty list HTTP 200, instead of throwing a HTTP 404 when it can't match a company via the Company Matching Service.
