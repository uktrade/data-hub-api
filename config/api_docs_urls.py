from django.contrib import admin
from django.urls import path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerSplitView,
)
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONOpenAPIRenderer


api_docs_urls = []
api_versions_to_document = ['v1', 'v3', 'v4']

for version in api_versions_to_document:
    api_docs_urls.extend([
        path(
            f'{version}/docs/schema',
            admin.site.admin_view(SpectacularAPIView.as_view(
                renderer_classes=[JSONOpenAPIRenderer],
                authentication_classes=[SessionAuthentication],
                permission_classes=[IsAuthenticated],
                api_version=f'api-{version}',
            )),
            name=f'openapi-schema-{version}',
        ),
        path(
            f'{version}/docs',
            admin.site.admin_view(SpectacularSwaggerSplitView.as_view(
                url_name=f'api-docs:openapi-schema-{version}',
                authentication_classes=[SessionAuthentication],
                permission_classes=[IsAuthenticated],
            )),
            name=f'swagger-ui-{version}',
        ),
    ])
