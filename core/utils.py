def generate_enum_code_from_constant_model(model_queryset):
    """Generate the Enum code for a given constant model queryset.

    Paste the generated text into the constants file.
    """

    for q in model_queryset:
        print("{} = Constant('{}', '{}')".format(q.name.replace(' ', '_').lower(), q.name, q.id))
