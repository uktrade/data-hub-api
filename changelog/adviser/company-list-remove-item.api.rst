The following endpoint was added:

  - ``DELETE /v4/company-list/<company list ID>/item/<company ID>``

This removes a company from the user's own selected list of companies.

If the operation is successful, a 204 status code will be returned. If there is no company list with specified company list ID or a list doesn't belong to the user, a 404 will be returned.
