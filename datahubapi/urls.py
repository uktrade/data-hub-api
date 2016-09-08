from django.conf.urls import include, url
from django.contrib import admin
from rest_framework import renderers, response, routers, schemas
from rest_framework.decorators import api_view, renderer_classes
from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer

from api.views.chcompanyviewset import CHCompanyViewSet
from api.views.companyviewset import CompanyViewSet
from api.views.contactviewset import ContactViewSet
from api.views.interationviewset import InteractionViewSet
from api.views.searchview import search


@api_view()
@renderer_classes([SwaggerUIRenderer, OpenAPIRenderer, renderers.CoreJSONRenderer])
def schema_view(request):
    generator = schemas.SchemaGenerator(title='Pastebin API')
    return response.Response(generator.get_schema(request=request))


router = routers.DefaultRouter()
router.register(r'ch', CHCompanyViewSet)
router.register(r'company', CompanyViewSet)
router.register(r'contact', ContactViewSet)
router.register(r'interaction', InteractionViewSet)

urlpatterns = [
    url(r'^search$', search),
    url('^$', schema_view),
    url(r'^', include(router.urls)),
    url(r'^admin/', admin.site.urls),
]
