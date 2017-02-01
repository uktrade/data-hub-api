from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from datahub.korben.connector import KorbenConnector


class CDMSUserBackend(ModelBackend):
    """Model backend that authenticates against CDMS and checks for whitelisting."""

    def korben_authenticate(self, username, password):
        """Authenticate CDMS user/advisor using korben."""
        conn = KorbenConnector()

        return conn.validate_credentials(username, password)

    def authenticate(self, username=None, password=None, **kwargs):
        """Copied from parent impl, but with password check done by Korben."""
        user_model = get_user_model()
        if username is None:
            username = kwargs.get(user_model.USERNAME_FIELD)
        try:
            user = user_model._default_manager.get_by_natural_key(username)
        except user_model.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            user_model().set_password(password)
        else:
            if self.user_can_authenticate(user):
                korben_auth_result = self.korben_authenticate(username,
                                                              password)
                if korben_auth_result:
                    # user authenticated via Korben
                    user.set_password(
                        password)  # cache passwd hash for backup auth
                    user.is_active = True  # ensure user can use django backend to auth, in case CDMS fails
                    user.save()

                    return user

                if korben_auth_result is False:
                    # User submitted wrong password, because it may have been changed in CDMS
                    # we need to erase passwd cache, otherwise old cached in django password would
                    # swill allow user in
                    user.set_unusable_password()
                    user.save()

    def user_can_authenticate(self, user):
        """Reject users that are not whitelisted."""
        return user.email.lower() in settings.DIT_ENABLED_ADVISORS
