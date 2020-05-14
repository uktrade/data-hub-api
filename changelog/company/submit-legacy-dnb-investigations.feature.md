A django management command `submit_legacy_dnb_investigations` was added to submit
remaining unsubmitted legacy investigations to D&B.  Companies are eligible
for submission through this command if they were created using the legacy
investigations API endpoint, have a telephone number recorded in `dnb_investigation_data`
and do not have a `website` set. Companies created through the legacy investigation endpoint
that do have a `website` have already been sent through to D&B outside of Data Hub.

This work enables us to deprecate and remove the `dnb_investigation_data` field
on Company.
