from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.serializers import ConstantModelSerializer
from .models import BusinessType, Country, EmployeeRange, InteractionType, Role, Title, UKRegion


@api_view()
def business_type(request):
    """List all business types."""
    serializer = ConstantModelSerializer(BusinessType.objects.all(), many=True)
    return Response(data=serializer.data)


@api_view()
def country(request):
    """List all countries."""
    serializer = ConstantModelSerializer(Country.objects.all(), many=True)
    return Response(data=serializer.data)


@api_view()
def employee_range(request):
    """List employee range options."""
    serializer = ConstantModelSerializer(EmployeeRange.objects.all(), many=True)
    return Response(data=serializer.data)


@api_view()
def interaction_type(request):
    """List all interaction types."""
    serializer = ConstantModelSerializer(InteractionType.objects.all(), many=True)
    return Response(data=serializer.data)


@api_view()
def role(request):
    """List all the roles."""
    serializer = ConstantModelSerializer(Role.objects.all(), many=True)
    return Response(data=serializer.data)


@api_view()
def title(request):
    """List all the titles."""
    serializer = ConstantModelSerializer(Title.objects.all(), many=True)
    return Response(data=serializer.data)


@api_view()
def uk_region(request):
    """List all the UK regions."""
    serializer = ConstantModelSerializer(UKRegion.objects.all(), many=True)
    return Response(data=serializer.data)


