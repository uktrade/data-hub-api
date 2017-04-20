class Mapping(object):
    def __init__(self, from_entitytype, ToModel, fields, undef=None, concat=None):
        self.from_entitytype = from_entitytype
        self.ToModel = ToModel
        self.fields = fields
        self.undef = undef
        if undef is not None:
            pass
        if concat is not None:
            pass
    def __contains__(self, field_name):
        return field_name in (x for _, x in self.fields)

class MetadataMapping(Mapping):
    def __init__(self, source_pkey, from_entitytype, name_field, ToModel):
        fields = (
            (source_pkey, 'id'),
            (name_field, 'name'),
        )
        super().__init__(from_entitytype, ToModel, fields)
