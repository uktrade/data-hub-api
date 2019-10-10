import logging

from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import Permission
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)


PAAS_ADDED_X_FORWARDED_FOR_IPS = 2


class TeamModelPermissionsBackend(ModelBackend):
    """Extension of CDMSUserBackend to include a team based permissions for user"""

    def _get_team_permissions(self, user_obj):
        """
        This method is called by the ModelBackend _get_permissions() dynamically
        as part of aggregating user, group and team permissions
        """
        if user_obj.dit_team and user_obj.dit_team.role:
            groups = user_obj.dit_team.role.groups.all()
        else:
            groups = []

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
            user_obj._perm_cache = self.get_user_permissions(user_obj).copy()
            user_obj._perm_cache.update(self.get_group_permissions(user_obj))
            user_obj._perm_cache.update(self.get_team_permissions(user_obj))
        return user_obj._perm_cache


class PaaSIPAuthentication(BaseAuthentication):
    """DRF authentication class that checks client IP addresses."""

    def authenticate_header(self, request):
        """
        This is returned as the WWW-Authenticate header when
        AuthenticationFailed is raised. DRF also requires this
        to send a 401 (as opposed to 403).
        """
        return 'PaaS IP'

    def authenticate(self, request):
        """
        Blocks incoming connections based on IP in X-Forwarded-For.

        Ideally, this would be done at the network level. However, this is
        not possible in PaaS.

        Given that production environments run on PaaS, the following rules are
        being implemented:

        - requests coming through Go Router or PaaS have the X-Forwarded-For header
          that contains at least two IP addresses, with the first one being the
          IP connection are made from, so we can check the second-from-the-end
          with some confidence it hasn't been spoofed.

        - requests originating from the internal network will not have X-Forwarded-For header

        If the IP address not allowed, AuthenticationFailed is raised.
        """
        if settings.DISABLE_PAAS_IP_CHECK:
            logger.warning('PaaS IP check authentication is disabled.')
            return None

        if 'HTTP_X_FORWARDED_FOR' not in request.META:
            # We assume that absence of the header indicates connection originating
            # in the internal network
            return None

        x_forwarded_for = request.META['HTTP_X_FORWARDED_FOR']
        ip_addresses = x_forwarded_for.split(',')

        if len(ip_addresses) < PAAS_ADDED_X_FORWARDED_FOR_IPS:
            logger.warning(
                'Failed access requirement: the X-Forwarded-For header does not '
                'contain enough IP addresses for external traffic',
            )
            raise AuthenticationFailed()

        # PaaS appends 2 IPs, where the IP connected from is the first
        remote_address = ip_addresses[-PAAS_ADDED_X_FORWARDED_FOR_IPS].strip()
        if remote_address not in settings.PAAS_IP_WHITELIST:
            logger.warning(
                'Failed access requirement: the X-Forwarded-For header was not '
                f'produced by a whitelisted IP - found {remote_address}',
            )
            raise AuthenticationFailed()

        return None
