"""Korben related exceptions."""


class KorbenException(Exception):
    """Generic Korben exception."""

    def __init__(self, message='Korben error.'):
        """Define message."""
        self.message = message
