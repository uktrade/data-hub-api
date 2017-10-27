from rest_framework.permissions import DjangoModelPermissions


class CrudPermission(DjangoModelPermissions):
    perms_map = DjangoModelPermissions.perms_map
    perms_map['GET'].append('%(app_label)s.read_%(model_name)s')

    def has_permission(self, request, view):
        return super().has_permission(request, view)
