class Mapping(object):

    def __init__(self, from_entitytype, ToModel, pk, fields, undef=None, concat=None):
        self.from_entitytype = from_entitytype
        self.ToModel = ToModel
        self.pk = pk
        self.fields = fields

        if undef is not None: self.undef = undef
        else: self.undef = ()

        if concat is not None: self.concat = concat
        else: self.concat = ()

    def values(self):
        return (x for _, x in self.fields)

    def keys(self):
        return (x for x, _ in self.fields)

    def __contains__(self, field_name):
        return field_name in self.values()

    def __getitem__(self, name):
        _, value = next(filter(lambda (key, value): key == name, self.fields))
        return value


class MetadataMapping(Mapping):
    def __init__(self, from_entitytype, ToModel, pk, name_field):
        fields = ((name_field, 'name'),)
        super().__init__(from_entitytype, ToModel, pk, fields)
