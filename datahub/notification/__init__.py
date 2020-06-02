"""Generic functionality for sending notifications (typically emails) via GOV.UK Notify."""

from datahub.notification.core import notify_gateway

__all__ = ('notify_gateway',)
