from unittest.mock import Mock

import factory
import pytest
from django.contrib.admin import site
from django.test import RequestFactory

from datahub.metadata.admin import ServiceAdmin
from datahub.metadata.models import Service
from datahub.metadata.test.factories import ServiceFactory


@pytest.mark.django_db
class TestServiceAdmin:
    """Tests for ServiceAdmin."""

    @pytest.mark.parametrize('context', (Service.Context.INTERACTION, Service.Context.EVENT))
    def test_context_filter(self, context):
        """Tests filtering by context."""
        test_data_contexts = (
            [Service.Context.INTERACTION],
            [Service.Context.SERVICE_DELIVERY],
            [Service.Context.INTERACTION, Service.Context.SERVICE_DELIVERY],
        )
        ServiceFactory.create_batch(
            len(test_data_contexts),
            contexts=factory.Iterator(test_data_contexts),
        )

        model_admin = ServiceAdmin(Service, site)
        request_factory = RequestFactory()
        request = request_factory.get(
            '/',
            data={'context': context},
        )
        request.user = Mock()
        change_list = model_admin.get_changelist_instance(request)

        actual_services = list(change_list.get_queryset(request))
        service_count_for_context = Service.objects.filter(contexts__overlap=[context]).count()
        assert len(actual_services) == service_count_for_context
        assert all(context in service.contexts for service in actual_services)

    def test_no_filter(self):
        """Test that if no filter is selected, all services are returned."""
        ServiceFactory.create_batch(5)

        model_admin = ServiceAdmin(Service, site)
        request_factory = RequestFactory()
        request = request_factory.get('/')
        request.user = Mock()
        change_list = model_admin.get_changelist_instance(request)

        actual_services = change_list.get_queryset(request)
        assert actual_services.count() == Service.objects.count()
