Error handling has now been added to the `datahub/company/consent.py` file's `get_many()` function. 
This change will be active when the Legal Basis API intergration is completed.
If the API returns a 500 error when retrieving contact marketing preferences, 
the contact's marketing preferences will be defaulted to False.