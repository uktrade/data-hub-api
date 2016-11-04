from django.apps import apps
from django.conf import settings
from django.core.management import BaseCommand

from company.models import Advisor


class Command(BaseCommand):
    help = 'Creates and attaches a User instance to all the Advisors without one.'

    def handle(self, *args, **options):
        orphan_advisors = Advisor.objects.filter(user__is_null=True)
        for advisor in orphan_advisors:
            user_model = apps.get_model(settings.AUTH_USER_MODEL)
            user = user_model.objects.create(
                email=advisor.email,
                first_name=advisor.first_name,
                last_name=advisor.last_name,
                username=advisor.email.split('@')[0],
            )
            user.set_unusable_password()
