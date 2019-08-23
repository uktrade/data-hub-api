from datahub.notification.tasks import send_email_notification


def notify_adviser_by_email(adviser, template_identifier, context, notify_service_name=None):
    """
    Notify an adviser by email, using a GOVUK notify template and some template
    context.
    """
    email_address = adviser.get_current_email()
    notify_by_email(email_address, template_identifier, context, notify_service_name)


def notify_contact_by_email(contact, template_identifier, context, notify_service_name=None):
    """
    Notify a contact by email, using a GOVUK notify template and some template
    context.
    """
    notify_by_email(contact.email, template_identifier, context, notify_service_name)


def notify_by_email(email_address, template_identifier, context, notify_service_name=None):
    """
    Notify an email address, using a GOVUK notify template and some template
    context.
    """
    kwargs = {'context': context}
    # TODO: Remove this check when we can assume that all celery workers will
    # accept a notify_service_name kwarg - after this has been released.
    if notify_service_name:
        kwargs['notify_service_name'] = notify_service_name
    send_email_notification.apply_async(
        args=(email_address, template_identifier),
        kwargs=kwargs,
    )
