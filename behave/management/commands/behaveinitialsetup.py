from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from oauth2_provider.models import Application

from datahub.metadata.models import Team


class Command(BaseCommand):
    help = 'Setup initials for Behave testing.'

    def setup_test_application(self):
        """Create a Oauth2 application."""
        client_secret = settings.API_CLIENT_SECRET
        client_id = settings.API_CLIENT_ID
        application_name = settings.APPLICATION_NAME
        user = self.setup_test_user()
        application = Application(
            user=user,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_PASSWORD,
            name=application_name,
            client_id=client_id,
            client_secret=client_secret
        )
        application.save()

    def setup_test_user(self):
        """Create a Django user."""
        user_model = get_user_model()
        test_user = settings.TEST_USERNAME.lower()
        test_user_password = settings.TEST_USER_PASSWORD
        user = user_model(
            email=test_user,
            first_name='Behave',
            last_name='User',
            is_active=True,
            dit_team=Team.objects.get(name='London International Trade Team')
        )
        user.set_password(test_user_password)
        user.save(skip_custom_validation=True)
        return user

    def add_cdms_user(self):
        """Add CDMS user to Django."""
        user_model = get_user_model()
        cdms_user = settings.CDMS_USERNAME.lower()
        user = user_model(
            first_name='CDMS',
            last_name='User',
            email=cdms_user,
            is_active=True,
            dit_team=Team.objects.get(name='London International Trade Team')
        )
        user.set_unusable_password()
        user.save(skip_custom_validation=True)

    def handle(self, *args, **options):
        """Handle function."""
        self.setup_test_application()
        self.add_cdms_user()
        self.stdout.write(self.style.SUCCESS('All done, happy testing'))
