A new endpoint `POST /v4/company/<company-id>/assign-regional-account-manager` has been added to allow users with `company.change_company and company.change_regional_account_manager` permissions to change the account manager of companies in the `Tier D - International Trade Advisers` One List Tier.

Example request body:
```
{ 
    "regional_account_manager": <adviser_uuid>
}
```

A successful request should expect an empty response with 204 (no content) HTTP status.