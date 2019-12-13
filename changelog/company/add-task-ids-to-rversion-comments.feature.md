Companies updated with the `update_company_from_dnb` command and the 
`update_companies_from_dnb_service` task are now saved with a reversion version
which has a meaningful identifier in the comment. This identifier will help provide
the groundwork for an "undo tool" which will allow us to reverse these automatic
updates in the event of a problem.
