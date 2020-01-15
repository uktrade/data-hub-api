A new Celery task called `automatic_company_archive` was added to Data Hub API.

This task would run every Saturday at 8pm in *simulation mode* with an upper limit of a *1000 companies*. In simulation mode, this task would log the IDs of the companies that would have been automatically archived using the following criteria:

- Do not have any OMIS orders
- Do not have any interactions during the last 8 years
- Not matched to any D&B records
- Not created or modified during the last 3 months
