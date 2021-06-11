from datahub.bed_api.factories import BedFactory
from datahub.bed_api.repositories import (
    AccountRepository,
    ContactRepository,
    EventAttendeeRepository,
    EventRepository,
    PolicyIssuesRepository,
)


class DataContext:
    """
    Represents the data context with all the consolidated repositories
    and functionality that can be applied to a data system
    """

    def __exit__(self, *args):
        """
        On exit after with context

        :param args:

        :return: DataContext instance
        """
        self.close_session()
        return self

    def close_session(self):
        """
        Close any active sessions or external infrastructure or resources
        needing clean up or closing
        """
        raise NotImplementedError


class BEDDataContext(DataContext):
    """
    Bed unit of work for interacting with the BED salesforce API
    """

    def __init__(self, session_factory_type=BedFactory):
        """
        Constructor

        :param session_factory_type:
        """
        super().__init__()
        self.session_factory_type = session_factory_type

    def __enter__(self):
        """
        Allows with statement to be used

        :return: BEDDataContext instance
        """
        self.salesforce = self.session_factory_type().create()
        self.contacts = ContactRepository(self.salesforce)
        self.accounts = AccountRepository(self.salesforce)
        self.interactions = EventRepository(self.salesforce)
        self.attendees = EventAttendeeRepository(self.salesforce)
        self.policy_issues = PolicyIssuesRepository(self.salesforce)
        return self

    def close_session(self):
        """
        Close session
        """
        if self.salesforce and self.salesforce.session:
            self.salesforce.session.close()
