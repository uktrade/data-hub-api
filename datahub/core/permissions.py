from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import DjangoModelPermissions


def method_permission_required(perm):
    def wrap(f):
        def wrapped_f(self, request, *args, **kwargs):
            if request.user.has_perm(perm):
                return f(self, request, *args, **kwargs)
            else:
                raise PermissionDenied
        return wrapped_f
    return wrap


class CrudPermission(DjangoModelPermissions):
    perms_map = DjangoModelPermissions.perms_map
    perms_map['GET'].append('%(app_label)s.read_%(model_name)s')

    def has_permission(self, request, view):
        return super().has_permission(request, view)
