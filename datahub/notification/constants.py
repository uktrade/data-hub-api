from enum import StrEnum


class NotifyServiceName(StrEnum):
    """Notify service name constants."""

    datahub = 'datahub'
    omis = 'omis'
    dnb_investigation = 'dnb_investigation'
    investment = 'investment'
    reminder = 'reminder'
    interaction = 'interaction'
    export_win = 'export_win'


DEFAULT_SERVICE_NAME = NotifyServiceName.datahub

# TODO: This module should not know or care about the specifics of our notify
# service instances. This should be moved up in to a setting. To ensure easy
# rollback, we will turn this on once OMIS integration no longer uses a feature
# flag.
NOTIFY_KEYS = {
    NotifyServiceName.datahub: 'DATAHUB_NOTIFICATION_API_KEY',
    NotifyServiceName.omis: 'OMIS_NOTIFICATION_API_KEY',
    NotifyServiceName.investment: 'INVESTMENT_NOTIFICATION_API_KEY',
    NotifyServiceName.interaction: 'INTERACTION_NOTIFICATION_API_KEY',
    NotifyServiceName.export_win: 'EXPORT_WIN_NOTIFICATION_API_KEY',
}
