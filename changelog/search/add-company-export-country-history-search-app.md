A search app `CompanyExportcountryHistory` was added to expose an API interface to the frontend. The app is supposed to 
aggregate data from both `CompanyExportCountryHistory` model and related `Interactions` data with the possibility to 
filter by `country.pk` and `company.pk`. The response should be in descending order by `history_date` datetime.  