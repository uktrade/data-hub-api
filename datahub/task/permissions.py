from rest_framework.permissions import BasePermission

from datahub.task.models import BaseTaskType


class IsAdviserPermittedToEditTask(BasePermission):
    """
    Permission class to limit edit access to a task to only the original creator, or to an adviser
    that has had the task assigned to them
    """

    def has_object_permission(self, request, view, obj):
        if request.method == 'PATCH':
            return self.validate_task_permission(request, view, obj)

        if (
            request.method == 'POST'
            and request.resolver_match.view_name == 'api-v4:task:task_archive'
        ):
            return self.validate_task_permission(request, view, obj)

        return True

    def validate_task_permission(self, request, view, obj):
        if obj.created_by.id == request.user.id:
            return True
        if isinstance(obj, BaseTaskType):
            if obj.task.advisers.filter(id=request.user.id).exists():
                return True
            return False
        if obj.advisers.filter(id=request.user.id).exists():
            return True

        return False
