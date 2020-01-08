The `datahub.dnb_api.tasks.get_company_updates` task now run with a specific list of fields to update by default.

This was introduced to not update `domain` & `registered_address` fields. This is because the data for these fields does not meet Data Hub standards. D&B have been informed of this and are working on a fix.
