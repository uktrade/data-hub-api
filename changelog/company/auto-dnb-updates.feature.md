A schedule was added for a nightly run of the celery task: `datahub.dnb_api.tasks.get_company_updates`.

This task will ingest D&B updates from `dnb_service`. The number of updates applied in a single run will be controlled by the environment variable called `DNB_AUTOMATIC_UPDATE_LIMIT`.
