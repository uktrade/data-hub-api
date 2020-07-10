For the Contacts CSV export endpoint (`GET /v3/search/contact/export`), this
makes it possible to get the `accepts_dit_email_marketing`
field from the Consent Service API. It will only lookup from the consent service if
the feature flag is enabled, otherwise no change.
