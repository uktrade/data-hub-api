The following endpoint was added:

- ``GET /v4/user/company-list/<company ID>``

It checks if a company is on the authenticated user's personal list of companies.

If the company is on the user's list, a 2xx status code will be returned. If it is not, a 404 will be returned.
