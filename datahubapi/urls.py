import coreapi
from django.conf.urls import url, include
from rest_framework import renderers, response, routers, schemas
from rest_framework.decorators import api_view, renderer_classes
from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer

from company.views import CompanyViewSet
from search.views import Search


router = routers.DefaultRouter()
router.register(r'company', CompanyViewSet)


@api_view()
@renderer_classes([SwaggerUIRenderer, OpenAPIRenderer, renderers.CoreJSONRenderer])
def schema_view(request):
    """Generate the OpenAPI schema to render the documentation."""
    generator = schemas.SchemaGenerator(title='Data hub API')
    document = generator.get_schema(request=request)

    # create manual doc for search endpoint
    search_content = {
        'search': coreapi.Link(
            url='/search',
            action='post',
            fields=[
                coreapi.Field(
                    name='term',
                    required=True,
                    location='body',
                    description='Search term.'
                ),
                coreapi.Field(
                    name='offset',
                    required=False,
                    location='body',
                    description='Offset the list of returned results by this amount. Default is zero.'
                ),
                coreapi.Field(
                    name='limit',
                    required=False,
                    location='body',
                    description='Number of items to retrieve. Default is 100.'
                )
            ],
            description='Return companies.'
        )
    }
    # extend document with manually created doc
    document = document.set_in(('search', ), search_content)
    return response.Response(document)


urlpatterns = [
    url('^$', schema_view),
    url(r'^', include(router.urls)),
    url(r'^search$', Search.as_view(), name='search'),
]
