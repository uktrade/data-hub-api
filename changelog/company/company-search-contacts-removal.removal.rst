The ``contacts`` field in company search results was removed from the following endpoints:

- ``/v3/search``
- ``/v3/search/company``
- ``/v4/search/company``

If you require a list of contacts for a company, please use ``/v3/contacts?company_id=<company ID>``
