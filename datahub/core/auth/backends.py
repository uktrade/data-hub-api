import logging

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import Permission
from pyquery import PyQuery

logger = logging.getLogger(__name__)


class CDMSInvalidCredentialsError(RuntimeError):
    """Thrown when CDMS credentials are invalid."""


class CDMSUserBackend(ModelBackend):
    """Model backend that authenticates against CDMS and checks for whitelisting."""

    def validate_cdms_credentials(self, user, username, password):
        """Authenticate CDMS user/adviser using cdms login page."""
        try:
            return self._cdms_login(
                url=settings.CDMS_AUTH_URL,
                username=username,
                password=password,
            ) is True  # No errors in the process assume success
        except requests.RequestException as exc:
            logger.exception('Connection error when communicating with CDMS auth server')
            if user.has_usable_password():
                # Indicate that the cached password should be used if there is one
                return None
            raise
        except (CDMSInvalidCredentialsError, AssertionError):
            return False  # Invalid credentials

    def authenticate(self, request, username=None, password=None, **kwargs):
        """Copied from parent impl, but with password check done by cdms."""
        user_model = get_user_model()
        if username is None:
            username = kwargs.get(user_model.USERNAME_FIELD)
        try:
            user = user_model._default_manager.get_by_natural_key(username)
        except user_model.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            user_model().set_password(password)
            return None
        else:
            if user.use_cdms_auth:
                auth_result = self.validate_cdms_credentials(user, username, password)
                if auth_result is True:
                    # user authenticated via CDMS
                    # cache passwd hash for backup auth
                    user.set_password(password)
                    # ensure user can use django backend to auth, in case CDMS fails
                    user.is_active = True
                    user.save()
                    return user

                if auth_result is False:
                    # User submitted wrong password, because it may have been changed in CDMS
                    # we need to erase passwd cache, otherwise old cached in django password would
                    # swill allow user in
                    user.set_unusable_password()
                    user.save()
                    return None

        # If cdms connection fails, fall back to local password check
        # or If user is not cdms user, use the default ModelBackend authenticate
        return super().authenticate(request, username, password, **kwargs)

    def user_can_authenticate(self, user):
        """Reject users that are not whitelisted."""
        return user.use_cdms_auth or super().user_can_authenticate(user)

    def _cdms_login(self, url, username, password, user_agent=None):
        """
        Login to the CDMS.

        This goes through the following steps:
        1. get login page
        2. submit the form with username and password
        3. the result is a form with a security token issued by the STS and the
           url of the next STS to validate the token
        4. submit the form of step 3. without making any changes
        5. repeat step 3. and 4 one more time to get the valid authentication
           cookie
        For more details, check:
        https://msdn.microsoft.com/en-us/library/aa480563.aspx
        """
        session = requests.session()
        if user_agent:
            session.headers.update({'User-Agent': user_agent})
        # 1. get login page
        # url = '{}/?whr={}'.format(CDMS_BASE_URL, CDMS_ADFS_URL)
        resp = session.get(url, timeout=settings.CDMS_AUTH_TIMEOUT)
        assert resp.ok

        html_parser = PyQuery(resp.text)
        username_field_name = html_parser('input[name*="Username"]').attr('name')
        password_field_name = html_parser('input[name*="Password"]').attr('name')

        # 2. submit the login form with username and password
        resp = self._submit_form(
            session, resp.content,
            url=resp.url,
            params={
                username_field_name: username,
                password_field_name: password})

        # 3. and 4. re-submit the resulting form containing the security token
        # so that the next STS can validate it
        resp = self._submit_form(session, resp.content)

        # 5. re-submit the form again to validate the token and get as result
        # the authenticated cookie
        resp = self._submit_form(session, resp.content)
        return resp.ok

    @staticmethod
    def _submit_form(session, source, url=None, params=None):
        """
        Submit CDMS STS form.

        It submits the form contained in the `source` param optionally
        overriding form `params` and form `url`.
        This is needed as UKTI has a few STSes and the token has to be
        validated by all of them.  For more details, check:
        https://msdn.microsoft.com/en-us/library/aa480563.aspx
        """
        html_parser = PyQuery(source)
        form_action = html_parser('form').attr('action')

        # get all inputs in the source + optional params passed in
        data = {
            field.get('name'): field.get('value')
            for field in html_parser('input')
        }
        data.update(params or {})

        url = url or form_action
        resp = session.post(url, data, timeout=settings.CDMS_AUTH_TIMEOUT)

        if not resp.ok:
            raise CDMSInvalidCredentialsError()

        html_parser = PyQuery(resp.content)
        assert form_action != html_parser('form').attr('action')

        return resp


class TeamModelPermissionsBackend(CDMSUserBackend):
    """Extension of CDMSUserBackend to include a team based permissions for user"""

    def _get_team_permissions(self, user_obj):
        """
        This method is called by the ModelBackend _get_permissions() dynamicaly
        as part of aggregating user, group and team permissions
        """
        groups = user_obj.dit_team.role.team_role_groups.all()
        return Permission.objects.filter(group__in=groups)

    def get_team_permissions(self, user_obj, obj=None):
        """
        Returns a set of permission strings the user `user_obj` has from the
        teams they belong to based on groups associated to team roles.
        """
        return self._get_permissions(user_obj, obj, 'team')

    def get_all_permissions(self, user_obj, obj=None):
        """
        Because of using cache in the parent class, its hard to extend using super()
        so the code is slightly duplicated
        """
        if not user_obj.is_active or user_obj.is_anonymous or obj is not None:
            return set()
        if not hasattr(user_obj, '_perm_cache'):
            user_obj._perm_cache = self.get_user_permissions(user_obj)
            user_obj._perm_cache.update(self.get_group_permissions(user_obj))
            user_obj._perm_cache.update(self.get_team_permissions(user_obj))
        return user_obj._perm_cache
