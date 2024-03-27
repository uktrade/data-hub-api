import pytest
from django.contrib.admin.sites import site as admin_site
from django.test import RequestFactory
from reversion.models import Version


from datahub.company.test.factories import AdviserFactory
from datahub.export_win.admin import (
    CustomerResponseInlineForm, DeletedWinAdmin, WinAdmin, WinAdminForm)
from datahub.export_win.models import DeletedWin, Win
from datahub.export_win.test.factories import CustomerResponseFactory, WinFactory


@pytest.fixture
def win():
    return WinFactory()


@pytest.fixture
def customer_response(win):
    return CustomerResponseFactory(name='Test Customer Response', win_id=win.id)


@pytest.mark.django_db
def test_get_actions_removes_delete_selected():
    """Test remove delete selected"""
    user = AdviserFactory()
    admin = WinAdmin(Win, admin_site)
    request = RequestFactory().get('/')
    request.user = user
    actions = admin.get_actions(request)
    assert 'delete_selected' not in actions


@pytest.mark.django_db
def test_soft_delete():
    """Test soft delete"""
    user = AdviserFactory()
    win1 = WinFactory()
    win2 = WinFactory()
    admin = WinAdmin(Win, None)
    request = RequestFactory().get('/')
    request.user = user
    queryset = Win.objects.filter(pk__in=[win1.pk, win2.pk])
    admin.soft_delete(request, queryset)
    win1.refresh_from_db()
    win2.refresh_from_db()
    assert win1.is_deleted is True
    assert win2.is_deleted is True

    for win in queryset:
        versions = Version.objects.get_for_object(win)
        assert len(versions) == 1
        assert versions[0].revision.comment == 'Soft deleted'


@pytest.mark.django_db
def test_undelete():
    """Test undelete"""
    user = AdviserFactory()
    deleted_win1 = WinFactory(is_deleted=True)
    deleted_win2 = WinFactory(is_deleted=True)
    request_factory = RequestFactory()
    request = request_factory.get('/')
    request.user = user
    admin = DeletedWinAdmin(model=DeletedWin, admin_site=None)
    admin.undelete(request, queryset=DeletedWin.objects.soft_deleted())
    deleted_win1.refresh_from_db()
    deleted_win2.refresh_from_db()
    assert deleted_win1.is_deleted is False
    assert deleted_win2.is_deleted is False


@pytest.mark.django_db
def test_name_field_not_required_and_readonly_when_instance_has_pk(customer_response):
    """Test fields not required and readonly within CustomerResponseInlineForm"""
    form = CustomerResponseInlineForm(instance=customer_response)
    assert form.fields['name'].required is False
    assert form.fields['id'].widget.attrs['readonly'] is True


@pytest.mark.django_db
def test_fields_not_required_when_instance_has_pk(win):
    """Test fields not required within WinFormTest"""
    form = WinAdminForm(instance=win)
    assert form.fields['cdms_reference'].required is False
    assert form.fields['customer_email_address'].required is False
    assert form.fields['customer_job_title'].required is False
    assert form.fields['line_manager_name'].required is False
    assert form.fields['lead_officer_email_address'].required is False
    assert form.fields['other_official_email_address'].required is False
