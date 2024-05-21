import functools
import json
from html.parser import HTMLParser

from rest_framework import status
from rest_framework.response import Response


class TagChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.contains_disallowed_content = False
        self.disallowed_tags = ['script', 'style', 'iframe', 'embed', 'object', 'form']
        self.disallowed_symbols = ['lt', 'gt', 'amp', 'quot', 'apos']
        self.disallowed_characters = ['<', '>', '\\']

    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.disallowed_tags:
            self.contains_disallowed_content = True

    def handle_endtag(self, tag):
        if tag.lower() in self.disallowed_tags:
            self.contains_disallowed_content = True

    def handle_data(self, data):
        if any(char in data for char in self.disallowed_characters):
            self.contains_disallowed_content = True

    def handle_entityref(self, name):
        if name.lower() in self.disallowed_symbols:
            self.contains_disallowed_content = True

    def handle_charref(self, name):
        self.contains_disallowed_content = True


def contains_script_or_html_tags(data):
    tag_checker = TagChecker()
    tag_checker.feed(data)
    return tag_checker.contains_disallowed_content


def validate_script_and_html_tags(view_method):
    @functools.wraps(view_method)
    def wrapper(self, request, *args, **kwargs):
        data_str = json.dumps(request.data)  # Assuming request.data is already a dictionary
        if contains_script_or_html_tags(data_str):
            return Response({'error': 'Input contains disallowed HTML or script tags or symbols'},
                            status=status.HTTP_400_BAD_REQUEST)
        return view_method(self, request, *args, **kwargs)
    return wrapper
