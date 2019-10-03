from typing import NamedTuple


class Version(NamedTuple):
    """A semantic version."""

    major: int
    minor: int
    patch: int

    @classmethod
    def from_dict(cls, dict_):
        """Create a version from a dict of version components."""
        components = [int(dict_[field]) for field in cls._fields]
        return cls(*components)

    def __str__(self):
        """Return a formatted (dot-separated) version."""
        return f'{self.major}.{self.minor}.{self.patch}'

    def increment_component(self, component):
        """Return the next major, minor or patch version."""
        component_index = self._fields.index(component)
        new_components = [
            _increment_version_component(index, self[index], component_index)
            for index in range(len(self._fields))
        ]

        return Version(*new_components)


def _increment_version_component(index, value, index_to_increment):
    """Increments a single version component in isolation."""
    if index < index_to_increment:
        return value

    if index == index_to_increment:
        return value + 1

    return 0
