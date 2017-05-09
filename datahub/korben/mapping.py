"""Convenience classes for mappings."""


class Mapping(object):
    """Container for spec of a mapping between CDMS entity and Django model."""

    def __init__(self, from_entitytype, ToModel, pk, fields, concat=None):  # noqa N803
        """Set up instance."""
        self.from_entitytype = from_entitytype
        self.ToModel = ToModel
        self.pk = pk
        self.fields = fields

        if concat is not None:
            self.concat = concat
        else:
            self.concat = ()

    def values(self):
        """Return LHS of self.fields."""
        return (x for _, x in self.fields)

    def keys(self):
        """Return RHS of self.fields."""
        return (x for x, _ in self.fields)

    def __contains__(self, field_name):
        """Is that Django field part of this mapping."""
        return field_name in self.values()

    def __getitem__(self, name):
        """Get CDMS name for Django field."""
        for key, value in self.fields:
            if value == name:
                return value


class MetadataMapping(Mapping):
    """Convenience class for mapping a metadata model."""

    def __init__(self, from_entitytype, ToModel, pk, name_field):  # noqa N803
        fields = ((name_field, 'name'),)
        super().__init__(from_entitytype, ToModel, pk, fields)
