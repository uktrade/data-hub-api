from django.conf import settings
from django.contrib.auth import get_user_model

from datahub.korben.connector import KorbenConnector


class CDMSUserBackend:
    """Model backend that authenticates against CDMS."""

    def korben_authenticate(self, username, password):
        """Authenticate CDMS user/advisor using korben."""
        conn = KorbenConnector()

        return conn.validate_credentials(username, password)

    def authenticate(self, username=None, password=None, **kwargs):
        """Copied from parent impl, but with password check done by Korben."""
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            UserModel().set_password(password)
        else:
            if self.user_can_authenticate(username) and self.korben_authenticate(username=username, password=password):
                    return user  # user authenticated via korben

    @staticmethod
    def user_can_authenticate(user):
        """Reject users that are not whitelisted."""
        return user.email.lower() in settings.DIT_ENABLED_ADVISORS

    def get_user(self, user_id):
        """Return the user object."""
        UserModel = get_user_model()
        try:
            user = UserModel._default_manager.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None
