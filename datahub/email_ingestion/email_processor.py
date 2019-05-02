from abc import ABC, abstractmethod


class EmailProcessor(ABC):
    """
    EmailProcessor subclasses should take a message and perform some actions
    based on it's metadata/content in order to process it.  EmailProcessor is
    an abstract superclass.
    """

    @abstractmethod
    def process_email(self, message):
        """
        Perform business logic to process a `mailparser.Message` instance - this
        may involve interacting with the DB or other services as necessary.

        :param message: mailparser.Message object - the email message to process

        :returns: Tuple of boolean (whether the message was successfully processed
            by this processor) and string (a meaningful message explaining why
            this was not processed or explaining that this was processed
            successfully).
            e.g.

            (False, "The email was not sent by a known DIT address")
        """
