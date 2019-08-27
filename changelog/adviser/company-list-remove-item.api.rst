The following endpoint was added:

  - ``DELETE /v4/company-list/<company list ID>/<company ID>``

  This removes a company from the user's own selected list of companies.

  If the operation is successful, a 2xx status code will be returned. If there is no company list with specified company list ID or company with the specified company ID, a 404 wil lbe returned.
