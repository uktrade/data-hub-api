The company hierarchy rollout task -
`datahub.dnb_api.tasks.sync_outdated_companies_with_dnb` - was adjusted so that
any failed sync tasks are not retried. This fixes a `RuntimeError` raised by
celery.
