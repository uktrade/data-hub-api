The following endpoint `PATCH /v4/company/<company-id>/update-one-list-core-team` expected user to have incorrect
permission. It has been corrected so that a user needs `change_company` and `change_one_list_core_team_member`
permissions to access it.
