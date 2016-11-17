from django.apps import apps
from django.conf import settings
from django.core.management import BaseCommand

from datahub.company.models import Advisor


class Command(BaseCommand):
    """Django command."""

    help = 'Creates and attaches a User instance to all the Advisors without one.'

    def handle(self, *args, **options):
        """Execute the command."""
        orphan_advisors = Advisor.objects.filter(user__isnull=True).exclude(first_name='Undefined')
        for advisor in orphan_advisors:
            user_model = apps.get_model(settings.AUTH_USER_MODEL)
            user = user_model.objects.create(
                email=advisor.email,
                first_name=advisor.first_name,
                last_name=advisor.last_name,
                username='{first_name}.{last_name}'.format(first_name=advisor.first_name, last_name=advisor.last_name),
            )
            user.set_unusable_password()
            advisor.user = user
            advisor.save(as_korben=True)  # dont' call Korben
            self.stdout('User created for advisor: {advisor}'.format(advisor=advisor.name))
