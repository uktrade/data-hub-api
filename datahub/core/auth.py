import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.serializers.json import DjangoJSONEncoder


from .utils import generate_signature


class KorbenConnector:
    """Korben connector."""

    default_headers = {
        'Content-type': 'application/json',
        'Accept': 'application/json',
    }

    def __init__(self):
        """Initalise the connector."""
        self._json_encoder = DjangoJSONEncoder()
        self.base_url = '{host}:{port}'.format(
            host=self.handle_host(settings.KORBEN_HOST),
            port=settings.KORBEN_PORT
        )

    @staticmethod
    def handle_host(host):
        """Add the protocol if not specified."""
        if 'http://' in host or 'https://' in host:
            return host
        else:
            return 'http://{host}'.format(host=host)

    def encode_json_bytes(self, model_dict):
        """Encode json into byte."""
        json_str = self._json_encoder.encode(model_dict)
        return bytes(json_str, 'utf-8')

    def inject_auth_header(self, url, body):
        """Add the signature into the header."""
        self.default_headers['X-Signature'] = generate_signature(url, body, settings.DATAHUB_SECRET)

    def validate_credentials(self, username, password):
        """Validate CDMS User credentials.

        :param username: str
        :param password: str
        :return: boolean success or fail, None if CDMS/Korben communication fails
        """
        url = '{base_url}/auth/validate-credentials/'.format(
            base_url=self.base_url,
        )
        data = self.encode_json_bytes(dict(username=username, password=password))
        self.inject_auth_header(url, data)
        try:
            response = requests.post(url=url, data=data, headers=self.default_headers)
            if response.ok:
                return response.json()  # Returns JSON encoded boolean
            else:
                return None
        except (requests.RequestException, ValueError):
            return None


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
                korben_auth_result = self.korben_authenticate(username, password)
                if korben_auth_result:
                    # user authenticated via Korben
                    user.set_password(password)  # cache passwd hash for backup auth
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
        return user.enabled
