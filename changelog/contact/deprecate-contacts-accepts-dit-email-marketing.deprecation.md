The `accepts_dit_email_marketing` field is deprecated and will be removed from the following contact endpoints:
- GET /v3/contact
- GET /v4/company
- GET /v4/company/{id}
- PATCH /v4/company/{id}
- POST /v3/contact/{id}/archive
- POST /v3/contact/{id}/unarchive

These end points will keep the `accepts_dit_email_marketing` field as the FE relies on it.
- POST /v3/contact 
- GET /v3/contact/{id}
- PATCH /v3/contact/{id} 
