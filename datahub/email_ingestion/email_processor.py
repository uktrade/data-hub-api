class EmailProcessor:

    def process_email(self, message):
        """
        """
        raise NotImplementedError(
            ("EmailProcessor subclass %s does not implement `process_email` "
                "method") % self.__class__.__name__
        )
