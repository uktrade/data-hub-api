The Celery tasks in `datahub.dnb_api.tasks` have been refactored into a package:

- `datahub.dnb_api.tasks.get_company_updates` is now `datahub.dnb_api.tasks.update.get_company_updates`
- `datahub.dnb_api.tasks.sync_outdated_companies_with_dnb` is now `datahub.dnb_api.tasks.sync.sync_outdated_companies_with_dnb`
