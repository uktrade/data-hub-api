from datahub.notification.tasks import send_email_notification


def notify_adviser_by_email(adviser, template_identifier, context):
    """
    Notify an adviser by email, using a GOVUK notify template and some template
    context.
    """
    email_address = adviser.get_current_email()
    send_email_notification.apply_async(
        args=(email_address, template_identifier),
        kwargs={'context': context},
    )


def notify_contact_by_email(contact, template_identifier, context):
    """
    Notify a contact by email, using a GOVUK notify template and some template
    context.
    """
    send_email_notification.apply_async(
        args=(contact.email, template_identifier),
        kwargs={'context': context},
    )
