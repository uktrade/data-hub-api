from django.http import HttpResponse
from rest_framework import status

from .services import services_to_check

PINGDOM_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<pingdom_http_custom_check>
    <status>{status}</status>
</pingdom_http_custom_check>\n"""

COMMENT_TEMPLATE = '<!--{comment}-->\n'


def ping(request):
    """Ping view."""
    checked = {}
    for service in services_to_check:
        checked[service.name] = service().check()

    if all(item[0] for item in checked.values()):
        return HttpResponse(
            PINGDOM_TEMPLATE.format(status='OK'),
            content_type='text/xml'
        )
    else:
        body = PINGDOM_TEMPLATE.format(status='FALSE')
        for service_result in filter(lambda x: x[0] is False, checked.values()):
            body += COMMENT_TEMPLATE.format(comment=service_result[1])
        return HttpResponse(
            body,
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content_type='text/xml'
        )
