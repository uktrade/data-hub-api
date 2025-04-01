from django.contrib import admin
from django.urls import path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerSplitView,
)
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONOpenAPIRenderer


def get_schema_and_docs_for_api_version(version: str):
    """Returns OpenAPI schema and Swagger UI for endpoints within a specific API version."""
    return [
        path(
            'docs/schema',
            admin.site.admin_view(
                SpectacularAPIView.as_view(
                    renderer_classes=[JSONOpenAPIRenderer],
                    authentication_classes=[SessionAuthentication],
                    permission_classes=[IsAuthenticated],
                    api_version=f'api-{version}',
                ),
            ),
            name=f'openapi-schema-{version}',
        ),
        path(
            'docs',
            admin.site.admin_view(
                SpectacularSwaggerSplitView.as_view(
                    url_name=f'api-{version}:openapi-schema-{version}',
                    authentication_classes=[SessionAuthentication],
                    permission_classes=[IsAuthenticated],
                ),
            ),
            name=f'swagger-ui-{version}',
        ),
    ]
