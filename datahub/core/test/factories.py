from functools import wraps

import factory
from oauth2_provider.models import AccessToken, Application


def to_many_field(wrapped_func):
    """Decorator which allows values of to-many fields to be easily set when using factory_boy.

    This is based on this example:
    http://factoryboy.readthedocs.io/en/latest/recipes.html#simple-many-to-many-relationship

    This avoids triggering deprecation warnings such as:

        RemovedInDjango20Warning: Direct assignment to the forward side of a many-to-many
        set is deprecated due to the implicit save() that happens. Use xxx.set() instead.

        RemovedInDjango20Warning: Direct assignment to the reverse side of a related set is
        deprecated due to the implicit save() that happens. Use xxx.set() instead.

    This decorator only calls the decorated function to get the default value if none has been
    explicitly provided.

    Example:

        class MyFactory(factory.django.DjangoModelFactory):
            ...
            @to_many_field
            def my_m2m_field(self):
                # return any default value
                return [ob1, obj2]

        Usage:
            fac = MyFactory(my_m2m_field=[obj3])  # creates an object with my_m2m_field == [obj3]
            fac = MyFactory()  # creates an object with my_m2m_field == [obj1, obj2]
    """
    @factory.post_generation
    @wraps(wrapped_func)
    def wrapping_func(self, create, extracted, **kwargs):
        if not create:
            # This means it's a 'build', which are unsaved so to-many values
            # should not be set
            return

        field = getattr(self, wrapped_func.__name__)
        if extracted is not None:
            field.set(extracted)
        else:
            # if the wrapped func returns a value, it's treated as a default value.
            value = wrapped_func(self)
            if value is not None:
                field.set(value)

    return wrapping_func


class ApplicationFactory(factory.django.DjangoModelFactory):
    """Application factory."""

    name = factory.Faker('words', nb=3)
    client_type = Application.CLIENT_CONFIDENTIAL
    authorization_grant_type = Application.GRANT_CLIENT_CREDENTIALS

    class Meta:  # noqa: D101
        model = Application


class OAuthApplicationScopeFactory(factory.django.DjangoModelFactory):
    """ApplicationScope factory."""

    application = factory.SubFactory(ApplicationFactory)

    class Meta:  # noqa: D101
        model = 'core.OAuthApplicationScope'


class AccessTokenFactory(factory.django.DjangoModelFactory):
    """AccessToken factory."""

    token = factory.Faker('password', length=20)
    expires = factory.Faker('date_time_between', start_date='+1d', end_date='+7d')

    class Meta:  # noqa: D101
        model = AccessToken
