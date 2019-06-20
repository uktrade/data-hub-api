from datahub.notification.tasks import send_email_notification


def notify_adviser_by_email(adviser, template_identifier, context):
    """
    Notify an adviser by email, using a GOVUK notify template and some template
    context.
    """
    send_email_notification.apply_async(args=(adviser.email, template_identifier, context))
