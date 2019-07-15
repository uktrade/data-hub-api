The following endpoint was added:

``DELETE /v4/user/company-list/<company ID>``

This removes a company from the authenticated user's personal list of companies.

If the operation is successful, a 2xx status code will be returned. If there is no company with the specified company ID, a 404 wil lbe returned.

Currently, the response body is unused.
