from rest_framework.permissions import DjangoModelPermissions


class CrudPermission(DjangoModelPermissions):
    """Extension of Permission class to include read permissions"""

    perms_map = DjangoModelPermissions.perms_map
    perms_map['GET'].append('%(app_label)s.read_%(model_name)s')
