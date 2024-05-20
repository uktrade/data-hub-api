import functools
import json
from html.parser import HTMLParser

from rest_framework import status

from rest_framework.response import Response


class TagChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.contains_tags = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() in ['script', 'style']:
            self.contains_tags = True

    def handle_endtag(self, tag):
        if tag.lower() in ['script', 'style']:
            self.contains_tags = True


def contains_script_or_html_tags(data):
    tag_checker = TagChecker()
    tag_checker.feed(data)
    return tag_checker.contains_tags


def validate_script_and_html_tags(view_method):
    @functools.wraps(view_method)
    def wrapper(self, request, *args, **kwargs):
        data_str = json.dumps(request.data)  # Assuming request.data is already a dictionary
        if contains_script_or_html_tags(data_str):
            return Response({'error': 'Input contains script or HTML tags'},
                            status=status.HTTP_400_BAD_REQUEST)
        return view_method(self, request, *args, **kwargs)
    return wrapper
