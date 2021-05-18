from datahub.bed_api.factories import BedFactory
from datahub.bed_api.repositories import (
    AccountRepository,
    ContactRepository,
    EventAttendeeRepository,
    EventRepository,
)


class UnitOfWork:
    """
    Base Unit of Work
    """

    def __exit__(self, *args):
        """
        On exit after with context
        :param args:
        :return: UnitOfWork instance
        """
        self.close_session()
        return self

    def close_session(self):
        """
        Close any active sessions
        """
        raise NotImplementedError


class BedUnitOfWork(UnitOfWork):
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
        :return: BedUnitOfWork instance
        """
        self.salesforce = self.session_factory_type().create()
        self.contacts = ContactRepository(self.salesforce)
        self.accounts = AccountRepository(self.salesforce)
        self.interactions = EventRepository(self.salesforce)
        self.attendees = EventAttendeeRepository(self.salesforce)
        return self

    def __exit__(self, *args):
        """
        Cleans up when the with is finalised
        :param args:
        """
        super().__exit__(*args)

    def close_session(self):
        """
        Close session
        """
        if self.salesforce and self.salesforce.session:
            self.salesforce.session.close()
