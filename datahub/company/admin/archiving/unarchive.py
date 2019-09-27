import django.contrib.messages as django_messages
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect


@method_decorator(csrf_protect)
def unarchive_company(model_admin, request):
    """
    Admin tool to unarchive a company.
    """
    if not model_admin.has_change_permission(request):
        raise PermissionDenied

    company = model_admin.get_object(request, request.GET.get('company'))

    if not company or company.archived is False:
        raise SuspiciousOperation()

    change_company_url = reverse(
        f'admin:{company._meta.app_label}_{company._meta.model_name}_change',
        args=[company.pk],
    )

    if company.transferred_to:
        error_message = (
            f'"{company.name}" has been merged with another company so it cannot be unarchived'
        )
        model_admin.message_user(request, error_message, django_messages.ERROR)
        return redirect(change_company_url)

    # Note: unarchive() saves the model instance
    company.unarchive()
    success_message = f'Successfully unarchived "{company.name}"'
    model_admin.message_user(request, success_message, django_messages.SUCCESS)
    return redirect(change_company_url)
