# Maintaining the API documentation

We make use of the built-in OpenAPI schema generation feature of Django Rest Framework. The feature is described in the following articles:

- https://www.django-rest-framework.org/topics/documenting-your-api/
- https://www.django-rest-framework.org/api-guide/schemas/

Swagger UI is served at ``/docs`` and a JSON OpenAPI schema at ``/docs/schema``.  

## Things to look out for when writing API views

The feature in DRF largely works by trying to introspect views. There are a few things to be aware of:

1. During introspection, generic view sets (in our code base, usually inheriting from `CoreViewSet`) will have their `get_serializer()` method (and, hence, `get_serializer_context()`) called without `self.kwargs` being populated. 
   
1. Where action methods are added to a generic view set (e.g. the `archive` and `unarchive` methods on many of our view sets), DRF will assume that the view set’s serializer is used for requests and responses.
    
    If this is wrong, the simplest thing to do is use the `datahub.core.schemas.StubSchema` to suppress request and response schema generation. See `datahub.omis.order.views.OrderViewSet` for an example.

1. [Generic view sets must specify a serializer class.](https://github.com/encode/django-rest-framework/issues/6535)
    
    If the view doesn’t, it’s not a generic view set and so you should use `APIView` instead. 

## Known limitations

1. `NestedRelatedField` is currently rendered as a string. Currently, all the logic pertaining to particular fields lies in DRF’s `AutoSchema` so this can’t be changed without replacing `AutoSchema`.

1. Pagination properties are missing from responses. This is a DRF limitation. 

1. Endpoints using `StubSchema` or `APIView` will be missing request and response schemas (where they have them).
      
   This could be overcome with [custom `AutoSchema` subclasses](https://www.django-rest-framework.org/api-guide/schemas/#per-view-customization). These could, for example, allow serializers to be explicitly specified or allow a schema in OpenAPI format to be explicitly specified (depending on the use case).
