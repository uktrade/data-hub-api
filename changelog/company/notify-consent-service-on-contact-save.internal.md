`.save` or `.update` using the ContactSerializer will trigger the `update_contact_consent`
celery task. This task is controlled by a feature flag UPDATE_CONSENT_SERVICE_FEATURE_FLAG
if that is not set this is essentially a no-op.
