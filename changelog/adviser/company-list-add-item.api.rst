The following endpoint was added:

  - ``PUT /v4/company-list/<company list ID>/item/<company ID>``

  This adds a company to the user's own selected list of companies.

  If the operation is successful, a 204 status code will be returned. If there is no company list with specified company list ID or company with the specified company ID, a 404 will be returned.

  If an archived company is specified, a 400 status code will be returned and response body will contain::

      {
          "non_field_errors": "An archived company can't be added to a company list."
      }

  Otherwise, the response body will be empty.
