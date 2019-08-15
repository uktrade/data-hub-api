DATAHUB_SERVICE_NAME = 'datahub'
OMIS_SERVICE_NAME = 'omis'

DEFAULT_SERVICE_NAME = DATAHUB_SERVICE_NAME

# TODO: This module should not know or care about the specifics of our notify
# service instances.  This should be moved up in to a setting.  To ensure easy
# rollback, we will turn this on once OMIS integration no longer uses a feature
# flag.
NOTIFY_KEYS = {
    DATAHUB_SERVICE_NAME: 'DATAHUB_NOTIFICATION_API_KEY',
    OMIS_SERVICE_NAME: 'OMIS_NOTIFICATION_API_KEY',
}
