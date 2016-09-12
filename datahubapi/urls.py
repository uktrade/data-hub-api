from django.conf.urls import include, url
from django.contrib import admin
from rest_framework import renderers, response, routers, schemas
from rest_framework.decorators import api_view, renderer_classes
from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer

@api_view()
@renderer_classes([SwaggerUIRenderer, OpenAPIRenderer, renderers.CoreJSONRenderer])
def schema_view(request):
    generator = schemas.SchemaGenerator(title='Pastebin API')
    return response.Response(generator.get_schema(request=request))


router = routers.DefaultRouter()

urlpatterns = [
    #url(r'^search$', search),
    url('^$', schema_view),
    url(r'^', include(router.urls)),
    url(r'^admin/', admin.site.urls),
]
