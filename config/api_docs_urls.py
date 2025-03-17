from django.contrib import admin
from django.urls import path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerSplitView,
)
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONOpenAPIRenderer


api_docs_urls = [
    path(
        'docs',
        admin.site.admin_view(SpectacularSwaggerSplitView.as_view(
            url_name='api-docs:openapi-schema',
            authentication_classes=[SessionAuthentication],
            permission_classes=[IsAuthenticated],
        )),
        name='swagger-ui',
    ),
    path(
        'docs/schema',
        admin.site.admin_view(SpectacularAPIView.as_view(
            renderer_classes=[JSONOpenAPIRenderer],
            authentication_classes=[SessionAuthentication],
            permission_classes=[IsAuthenticated],
            api_version='api-v3',  # TODO: Get working with multiple API versions
        )),
        name='openapi-schema',
    ),
]
