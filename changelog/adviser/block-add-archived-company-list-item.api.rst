``PUT /v4/user/company-list/<company ID>``: A 400 is now returned if an archived company is specified.

In this case, the response body will contain::

    {
        "non_field_errors": "An archived company can't be added to a company list."
    }

(Note that it is still possible to remove archived companies from a user's company list.)
