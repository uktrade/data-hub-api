from functools import wraps

import factory


def to_many_field(wrapped_func):
    """Decorator which allows values of to-many fields to be easily set when using factory_boy.

    This is based on this example:
    http://factoryboy.readthedocs.io/en/latest/recipes.html#simple-many-to-many-relationship

    This avoids triggering deprecation warnings such as:

        RemovedInDjango20Warning: Direct assignment to the forward side of a many-to-many
        set is deprecated due to the implicit save() that happens. Use xxx.set() instead.

        RemovedInDjango20Warning: Direct assignment to the reverse side of a related set is
        deprecated due to the implicit save() that happens. Use xxx.set() instead.

    This decorator doesn't call the decorated function; the decorated function is only used
    for its name.
    """
    @factory.post_generation
    @wraps(wrapped_func)
    def wrapping_func(self, create, extracted, **kwargs):
        if not create:
            # This means it's a 'build', which are unsaved so to-many values
            # should not be set
            return

        if extracted:
            field = getattr(self, wrapped_func.__name__)
            field.set(extracted)

    return wrapping_func
