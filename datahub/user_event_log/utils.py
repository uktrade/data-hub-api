from datahub.user_event_log.models import UserEvent


def record_user_event(request, type_, data=None):
    """Records a user event in the database."""
    event = UserEvent(
        adviser=request.user,
        type=type_,
        api_url_path=request.path,
        data=data,
    )
    event.save()
    return event
