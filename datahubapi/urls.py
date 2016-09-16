from django.conf.urls import url
from rest_framework import renderers, response, routers, schemas
from rest_framework.decorators import api_view, renderer_classes
from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer

from search.views import Search

@api_view()
@renderer_classes([SwaggerUIRenderer, OpenAPIRenderer, renderers.CoreJSONRenderer])
def schema_view(request):
    generator = schemas.SchemaGenerator(title='Data hub API')
    return response.Response(generator.get_schema(request=request))


router = routers.DefaultRouter()

urlpatterns = [
    url(r'^search$', Search.as_view(), name='search'),
    url('^$', schema_view),
]
