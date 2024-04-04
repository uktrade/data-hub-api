from unittest.mock import Mock

import pytest

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group
from django.test import RequestFactory
from reversion.models import Version

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.export_win.admin import (
    AdvisorInlineForm,
    BreakdownInlineForm,
    CustomerResponseInlineForm,
    DeletedWinAdmin, WinAdmin,
    WinAdminForm,
    WinSoftDeletedAdminForm)
from datahub.export_win.models import DeletedWin, Win
from datahub.export_win.test.factories import CustomerResponseFactory, WinFactory


@pytest.fixture
def win():
    return WinFactory()


@pytest.fixture
def customer_response(win: WinFactory):
    return CustomerResponseFactory(name='Test Customer Response', win_id=win.id)


@pytest.mark.django_db
def test_get_actions():
    """Test for actions"""
    user = AdviserFactory()
    admin = WinAdmin(Win, AdminSite())
    request_factory = RequestFactory()
    request = request_factory.get('/')
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
    queryset = DeletedWin.objects.soft_deleted()
    admin.undelete(request, queryset)
    deleted_win1.refresh_from_db()
    deleted_win2.refresh_from_db()
    assert deleted_win1.is_deleted is False
    assert deleted_win2.is_deleted is False

    for win in queryset:
        versions = Version.objects.get_for_object(win)
        assert len(versions) == 1
        assert versions[0].revision.comment == 'Undeleted'


@pytest.mark.django_db
def test_get_queryset_soft_deleted():
    """Test for get softdeleted queryset"""
    WinFactory(is_deleted=True)
    WinFactory(is_deleted=True)
    WinFactory(is_deleted=False)
    WinFactory(is_deleted=False)

    admin = DeletedWinAdmin(DeletedWin, AdminSite())
    request_factory = RequestFactory()
    request = request_factory.get('/admin/')
    queryset = admin.get_queryset(request)

    assert queryset.count() == 2
    assert all(obj.is_deleted for obj in queryset)


@pytest.mark.django_db
def test_get_company():
    """Test for get company"""
    company = CompanyFactory()
    admin = WinAdmin(model=Win, admin_site=AdminSite())
    obj = WinFactory(company=company)
    result = admin.get_company(obj)

    assert result == company


@pytest.mark.django_db
def test_get_adviser():
    """Test for get adviser"""
    adviser = AdviserFactory()
    admin = WinAdmin(model=Win, admin_site=AdminSite())
    obj = WinFactory(adviser=adviser)
    result = admin.get_adviser(obj)

    expected_result = f'{adviser} <{adviser.email}>'
    assert result == expected_result


@pytest.mark.django_db
def test_get_date_confirmed():
    """Test for get date confirmed"""
    customer_response = CustomerResponseFactory(responded_on='2024-04-01')
    admin = WinAdmin(model=Win, admin_site=AdminSite())
    obj = WinFactory(customer_response=customer_response)
    result = admin.get_date_confirmed(obj)

    expected_result = '2024-04-01'
    assert result == expected_result


@pytest.mark.django_db
def test_get_contact_names():
    """Test for get contact names"""
    contact1 = ContactFactory(first_name='John', last_name='Doe')
    contact2 = ContactFactory(first_name='Jane', last_name='Smith')
    obj = WinFactory()
    obj.company_contacts.add(contact1, contact2)

    admin = WinAdmin(model=Win, admin_site=AdminSite())
    result = admin.get_contact_names(obj)

    expected_result = 'John Doe, Jane Smith'
    assert result == expected_result


@pytest.mark.django_db
def test_has_view_permission():
    """Test for has view permission in deleted win"""
    regular_user = AdviserFactory()
    export_win_admin_group = Group.objects.create(name='ExportWinAdmin')
    regular_user.groups.add(export_win_admin_group)

    superuser = AdviserFactory(is_superuser=True)
    admin = DeletedWinAdmin(Win, AdminSite())
    request = RequestFactory().get('/')

    request.user = regular_user
    assert admin.has_view_permission(request) is True

    request.user = AdviserFactory()
    assert admin.has_view_permission(request) is False

    request.user = superuser
    assert admin.has_view_permission(request) is True


@pytest.mark.django_db
class TestWinSoftDeletedAdminForm:
    """Test for WinSoftDeletedAdminForm"""

    def test_init_method(self):
        form = WinSoftDeletedAdminForm()
        assert form is not None


@pytest.mark.django_db
class TestWinAdminForm:
    """Test for WinAdminForm"""

    def test_init_method(self):
        form = WinAdminForm()
        assert form is not None

    def test_init_method_with_instance_pk(self):
        instance_mock = InstanceMock(pk=1)
        form = WinAdminForm(instance=instance_mock)
        assert form is not None
        if instance_mock.pk is not None:
            field_attrs = form.fields['total_expected_export_value'].widget.attrs
            assert field_attrs['readonly'] == 'readonly'
            field_attrs = form.fields['total_expected_non_export_value'].widget.attrs
            assert field_attrs['readonly'] == 'readonly'
            field_attrs = form.fields['total_expected_odi_value'].widget.attrs
            assert field_attrs['readonly'] == 'readonly'
            assert form.fields['cdms_reference'].required is False
            assert form.fields['customer_email_address'].required is False
            assert form.fields['customer_job_title'].required is False
            assert form.fields['line_manager_name'].required is False
            assert form.fields['lead_officer_email_address'].required is False
            assert form.fields['other_official_email_address'].required is False


@pytest.mark.django_db
class TestWinBreakdownInlineForm:
    """Test for Breakdown in line form"""

    def test_init_method(self):
        form = BreakdownInlineForm()
        assert form is not None


@pytest.mark.django_db
class TestAdvisorInlineForm:
    """Test for Adviser in line form"""

    def test_init_method(self):
        form = AdvisorInlineForm()
        assert form is not None


class InstanceMock:
    def __init__(self, pk):
        self.pk = pk

    @property
    def _meta(self):
        return type('Meta', (),
                    {'fields': [],
                     'exclude': [],
                     'concrete_fields': [],
                     'private_fields': [], 'many_to_many': []})


@pytest.mark.django_db
class TestCustomerResponseInlineForm:
    """
    Test for Customer Response in line form
    Field name is not required and field id should be read-only
    """

    def test_init_method(self):
        instance_mock = InstanceMock(pk=1)
        form = CustomerResponseInlineForm(instance=instance_mock)
        assert form is not None
        if instance_mock and instance_mock.pk:
            assert form.fields['name'].required is False
            assert form.fields['id'].widget.attrs['readonly'] is True


@pytest.mark.django_db
class TestWinAdminSearchResults:

    def test_admin_search_no_filters(self):
        win1 = WinFactory()
        contacts = ContactFactory.create_batch(4)
        win1.company_contacts.set(contacts)
        WinFactory()

        admin = WinAdmin(Win, None)
        results = admin.get_search_results(Mock(), Win.objects.all(), '')[0]

        assert len(results) == 2

    def test_admin_search_on_adviser_name(self):
        adviser = AdviserFactory(first_name='FIRST', last_name='LAST')
        win1 = WinFactory(adviser=adviser)
        WinFactory.create_batch(3)
        admin = WinAdmin(Win, None)
        results = admin.get_search_results(Mock(), Win.objects.all(), 'FIRST LAST')[0]

        assert len(results) == 1
        assert results[0].id == win1.id

    def test_admin_search_on_lead_officer_name(self):
        lead_officer = AdviserFactory(first_name='LEAD', last_name='OFFICER')
        win1 = WinFactory(lead_officer=lead_officer)
        WinFactory.create_batch(3)
        admin = WinAdmin(Win, None)
        results = admin.get_search_results(Mock(), Win.objects.all(), 'LEAD OFFICER')[0]

        assert len(results) == 1
        assert results[0].id == win1.id

    def test_admin_search_on_contact_name(self):
        contact1 = ContactFactory(first_name='John', last_name='Doe')
        contact2 = ContactFactory(first_name='Jane', last_name='Smith')

        win1 = WinFactory()
        win1.company_contacts.add(contact1, contact2)

        WinFactory.create_batch(3)
        admin = WinAdmin(Win, None)
        results = admin.get_search_results(Mock(), Win.objects.all(), 'John Doe')[0]

        assert len(results) == 1
        assert results[0].id == win1.id
