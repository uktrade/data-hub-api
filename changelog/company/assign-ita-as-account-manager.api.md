A new endpoint, `POST /v4/company/<ID>/self-assign-account-manager`, was added. It:

- sets the authenticated user as the One List account manager
- sets the One List tier of the company to 'Tier D - Interaction Trade Adviser Accounts'

The operation is not allowed if:

- the company is a subsidiary of a One List company (on any tier)
- the company is already a One List company on a different tier (i.e. not 'Tier D - Interaction Trade Adviser Accounts')

The `company.change_company` and `company.change_regional_account_manager` permissions are required to use this endpoint.
