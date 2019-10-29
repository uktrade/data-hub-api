A new endpoint, `POST /v4/company/<ID>/remove-account-manager`, was added. 

The endpoint removes the assigned tier and account manager for a One List company on tier 'Tier D - Interaction Trade Adviser Accounts'.

If the company is on a One List tier other than 'Tier D - Interaction Trade Adviser Accounts', the operation is not allowed.

The `company.change_company` and `company.change_regional_account_manager` permissions are required to use this endpoint.
