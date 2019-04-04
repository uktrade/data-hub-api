class EmailProcessor:
    """
    EmailProcessor subclasses should take a message and perform some actions
    based on it's metadata/content in order to process it.  EmailProcessor is
    an abstract superclass.
    """

    def process_email(self, message):
        """
        Perform business logic to process a `mailparser.Message` instance - this
        may involve interacting with the DB or other services as necessary.

        Args:
          * ``message`` - mailparser.Message object - the email message to process

        Returns:
          Tuple of boolean (whether the message was successfully processed
          by this processor) and string (a meaningful message explaining why
          this was not processed or explaining that this was processed
          successfully).
          e.g.

          (False, "The email was not sent by a known DIT address")

        """
        raise NotImplementedError(
            (
                'EmailProcessor subclass %s does not implement `process_email` '
                'method'
            ) % self.__class__.__name__,
        )
