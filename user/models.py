from django.contrib.auth.models import AbstractUser
from django.utils.functional import cached_property


class User(AbstractUser):

    @cached_property
    def name(self):
        return '{first_name} {last_name}'.format(first_name=self.first_name, last_name=self.last_name)

    def __str__(self):
        return self.name
