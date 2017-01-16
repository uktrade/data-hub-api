"""Korben related exceptions."""


class KorbenException(Exception):
    """Generic Korben exception."""

    def __init__(self, message='Korben Error'):
        """Define message."""
        self.message = message
