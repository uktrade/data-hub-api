It is now possible to set `GET_CONSENT_FROM_CONSENT_SERVICE` feature flag to active
to enable looking up `Contact.accepts_dit_email_marketing` from central Consent
Service API when making a call to ContactsDataView
(`GET /v4/dataset/contacts-dataset`) which is used for exporting Data Hub's entire
list of contacts to Data Workspace.
