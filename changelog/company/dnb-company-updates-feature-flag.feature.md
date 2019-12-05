A feature flag was added `"dnb-company-updates"` which governs whether or not to
run the logic within the `datahub.dnb_api.tasks.get_company_updates` celery task.
This affords us the ability to easily switch on/off DNB company updates as needed 
during the rollout of this feature.
