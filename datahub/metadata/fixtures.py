import inspect
from pathlib import PurePath

_registry = []


class Fixture:
    """Class to register metadata fixtures."""

    files = []

    @classmethod
    def __init_subclass__(cls, **kwargs):
        """Called on class declaration to register the class's fixtures."""
        super().__init_subclass__(**kwargs)
        directory_path = PurePath(inspect.getsourcefile(cls)).parent
        _registry.extend(directory_path / file for file in cls.files)

    @classmethod
    def all(cls):
        """
        Returns a list of all registered fixtures.

        Should only be called after apps have loaded the metadata app's ready() method has been
        called.
        """
        return _registry
