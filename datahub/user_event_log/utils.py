from datahub.user_event_log.models import UserEvent


def record_user_event(request, type_, adviser=None, data=None):
    """Records a user event in the database."""
    return UserEvent.objects.create(
        adviser=adviser or request.user,
        type=type_,
        api_url_path=request.path,
        data=data,
    )
