from django.http import HttpResponse

PINGDOM_TEMPLATE = """<pingdom_http_custom_check>
    <status>{status}</status>
    <response_time>{time}</response_time>
</pingdom_http_custom_check>"""


def ping(request):
    return HttpResponse('content', content_type='text/xml')