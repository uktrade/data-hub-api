The following endpoint `GET /v4/dataset/contacts-dataset` returns an error 500 when the `GET_CONSENT_FROM_CONSENT_SERVICE` is active. This is due to emails not be valid in the database.
This bugfix will strip out invalid emails before sending emails as payload.
