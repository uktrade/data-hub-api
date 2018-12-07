
from django.apps import AppConfig


class MIDashboardConfig(AppConfig):
    """
    Django App Config for the MI Dashboard app.
    """

    name = 'datahub.mi_dashboard'

    # this label is being used by the db_router to determine if migration is allowed for given
    # database
    label = 'datahub.mi_dashboard'
