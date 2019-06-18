from datahub.notification.tasks import send_email_notification


def notify_adviser(adviser, template_identifier, context):
    send_email_notification.apply_async(args=(adviser.email, template_identifier, context))
