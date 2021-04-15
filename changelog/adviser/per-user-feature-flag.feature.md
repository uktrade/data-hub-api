Feature flags can now be applied on a per-user basis through Django Admin.

- Adds a new UserFeatureFlag model
- Adds a new "features" field to the Advisor model
- Exposes "active_features" on the `whoami` endpoint
