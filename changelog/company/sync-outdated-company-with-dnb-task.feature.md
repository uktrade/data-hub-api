A celery task `datahub.dnb_api.tasks.sync_outdated_companies_with_dnb` was added
which provides a mechanism for syncing fields on outdated Data Hub company records
with D&B.
This can be used to "backfill" older Company records with newly recorded D&B
data; e.g. for rolling out company hierarchies to all D&B linked companies
by syncing the `global_ultimate_duns_number` field.
