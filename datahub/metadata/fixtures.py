import inspect
from pathlib import PurePath

_registry = []


class FixtureMeta(type):
    """
    Metaclass for metadata fixtures.

    Used to auto-register metadata fixtures.
    """

    def __new__(mcs, name, bases, namespace, **kwargs):  # noqa: N804
        """
        Creates the metaclass instance.

        Called on Fixture subclass declaration.
        """
        cls = type.__new__(mcs, name, bases, namespace)
        cls.register()
        return cls


class Fixture(metaclass=FixtureMeta):
    """Class to register metadata fixtures."""

    files = []

    @classmethod
    def register(cls):
        """Called on class declaration to register the class's fixtures."""
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
