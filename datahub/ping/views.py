from datetime import datetime

from django.http import HttpResponse
from rest_framework import status

from .services import services_to_check

PINGDOM_TEMPLATE = """<pingdom_http_custom_check>
    <status>{status}</status>
    <response_time>{time}</response_time>
</pingdom_http_custom_check>"""

COMMENT_TEMPLATE = '<!--{comment}-->'


def ping(request):
    start = datetime.now()
    checks = {}
    for service in services_to_check:
        checks[service.name] = service.check()

    end = datetime.now()
    elapsed_time = end - start

    if all(checks.items()):
        return HttpResponse(
            PINGDOM_TEMPLATE.format(status='OK', time=elapsed_time.seconds()),
            content_type='text/xml'
        )
    else:
        PINGDOM_TEMPLATE.format(status='FALSE', time=elapsed_time.seconds()),
        return HttpResponse(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )