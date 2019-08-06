from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from rest_framework.authentication import SessionAuthentication
from rest_framework.renderers import JSONOpenAPIRenderer
from rest_framework.schemas import get_schema_view


API_DOCUMENTATION_TITLE = 'Data Hub API'
API_DOCUMENTATION_DESCRIPTION = """Auto-generated API documentation for Data Hub.

There are currently some missing or incorrect details as we are limited by the web framework
we are using. These should be corrected over time as the relevant features in the framework are
enhanced.
"""


api_docs_urls = [
    path(
        'docs',
        admin.site.admin_view(
            TemplateView.as_view(
                template_name='core/docs/swagger-ui.html',
                extra_context={
                    'swagger_ui_css': settings.SWAGGER_UI_CSS,
                    'swagger_ui_js': settings.SWAGGER_UI_JS,
                },
            ),
        ),
        name='swagger-ui',
    ),
    path(
        'docs/schema',
        get_schema_view(
            title=API_DOCUMENTATION_TITLE,
            description=API_DOCUMENTATION_DESCRIPTION,
            # JSONOpenAPIRenderer works better with IntEnum, StrEnum etc.
            renderer_classes=[JSONOpenAPIRenderer],
            authentication_classes=[SessionAuthentication],
        ),
        name='openapi-schema',
    ),
]
