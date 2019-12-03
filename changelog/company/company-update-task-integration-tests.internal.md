Integration tests were added for the `datahub.dnb_api.tasks.get_company_updates` task.
These were not added as part of the original development as the task and it's dependent
task (`datahub.dnb_api.tasks.update_company_from_dnb_data`) were developed in parallel.

Additionally, the calls that `datahub.dnb_api.tasks.get_company_updates` makes to
`datahub.dnb_api.tasks.update_company_from_dnb_data` were fixed to be the correct
signature.
