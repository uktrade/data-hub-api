A new `POST /v4/company/<company-id>/assign-one-list-tier-and-global-account-manager` endpoint to assign One List tier
and a global account manager to Company has been added. Adviser with correct permissions can assign any tier except
`Tier D - International Trade Adviser Accounts`.

The endpoint expects following JSON body:

```
{
    "one_list_tier": <One List tier UUID>,
    "global_account_manager": <adviser ID>
}
```
