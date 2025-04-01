import functools
import json
from html.parser import HTMLParser

from rest_framework import status
from rest_framework.response import Response

DISALLOWED_TAGS = ['script', 'style', 'iframe', 'embed', 'object', 'form']
DISALLOWED_SYMBOLS = ['lt', 'gt', 'amp', 'quot', 'apos']
DISALLOWED_CHARACTERS = ['<', '>']


class TagChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.contains_disallowed_content = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() in DISALLOWED_TAGS:
            self.contains_disallowed_content = True

    def handle_endtag(self, tag):
        if tag.lower() in DISALLOWED_TAGS:
            self.contains_disallowed_content = True

    def handle_data(self, data):
        if any(char in data for char in DISALLOWED_CHARACTERS):
            self.contains_disallowed_content = True

    def handle_entityref(self, name):
        if name.lower() in DISALLOWED_SYMBOLS:
            self.contains_disallowed_content = True

    def handle_charref(self, name):
        self.contains_disallowed_content = True


def contains_disallowed_content(data):
    if any(char in data for char in DISALLOWED_CHARACTERS):
        return True
    tag_checker = TagChecker()
    tag_checker.feed(data)
    return tag_checker.contains_disallowed_content


def validate_script_and_html_tags(view_method):
    @functools.wraps(view_method)
    def wrapper(self, request, *args, **kwargs):
        data_str = request.data if isinstance(request.data, str) else json.dumps(request.data)
        if contains_disallowed_content(data_str):
            return Response(
                {'error': 'Input contains disallowed HTML or script tags or symbols'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return view_method(self, request, *args, **kwargs)

    return wrapper
