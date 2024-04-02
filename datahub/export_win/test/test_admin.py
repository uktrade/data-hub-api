import pytest

from django.contrib.admin.sites import AdminSite
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
def customer_response(win):
    return CustomerResponseFactory(name='Test Customer Response', win_id=win.id)


@pytest.mark.django_db
def test_get_actions():
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
def test_fields_not_required_when_instance_has_pk(win):
    """Test fields not required within WinFormTest"""
    form = WinAdminForm(instance=win)
    assert form.fields['cdms_reference'].required is False
    assert form.fields['customer_email_address'].required is False
    assert form.fields['customer_job_title'].required is False
    assert form.fields['line_manager_name'].required is False
    assert form.fields['lead_officer_email_address'].required is False
    assert form.fields['other_official_email_address'].required is False


@pytest.mark.django_db
def test_get_queryset_soft_deleted():
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
    company = CompanyFactory()
    admin = WinAdmin(model=Win, admin_site=AdminSite())
    obj = WinFactory(company=company)
    result = admin.get_company(obj)

    assert result == company


@pytest.mark.django_db
def test_get_adviser():
    adviser = AdviserFactory()
    admin = WinAdmin(model=Win, admin_site=AdminSite())
    obj = WinFactory(adviser=adviser)
    result = admin.get_adviser(obj)

    expected_result = f'{adviser} <{adviser.email}>'
    assert result == expected_result


@pytest.mark.django_db
def test_get_date_confirmed():
    customer_response = CustomerResponseFactory(responded_on='2024-04-01')
    admin = WinAdmin(model=Win, admin_site=AdminSite())
    obj = WinFactory(customer_response=customer_response)
    result = admin.get_date_confirmed(obj)

    expected_result = '2024-04-01'
    assert result == expected_result


@pytest.mark.django_db
def test_get_contact_names():
    contact1 = ContactFactory(first_name='John', last_name='Doe')
    contact2 = ContactFactory(first_name='Jane', last_name='Smith')
    obj = WinFactory()
    obj.company_contacts.add(contact1, contact2)

    admin = WinAdmin(model=Win, admin_site=AdminSite())
    result = admin.get_contact_names(obj)

    expected_result = 'John Doe, Jane Smith'
    assert result == expected_result


@pytest.mark.django_db
class TestWinSoftDeletedAdminForm:
    def test_init_method(self):
        form = WinSoftDeletedAdminForm()
        assert form is not None


@pytest.mark.django_db
class TestWinAdminForm:
    def test_init_method(self):
        form = WinAdminForm()
        assert form is not None


@pytest.mark.django_db
class TestWinBreakdownInlineForm:
    def test_init_method(self):
        form = BreakdownInlineForm()
        assert form is not None


@pytest.mark.django_db
class TestAdvisorInlineForm:
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
    def test_init_method(self):
        instance_mock = InstanceMock(pk=1)
        form = CustomerResponseInlineForm(instance=instance_mock)
        assert form is not None
        if instance_mock and instance_mock.pk:
            assert form.fields['name'].required is False
            assert form.fields['id'].widget.attrs['readonly'] is True
