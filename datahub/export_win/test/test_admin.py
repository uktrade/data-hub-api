import uuid
from unittest.mock import Mock

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group
from django.test import RequestFactory
from reversion.models import Version

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.export_win.admin import (
    AdvisorInlineForm,
    AnonymousWinAdminForm,
    BreakdownInlineForm,
    CustomerResponseInlineForm,
    DeletedWinAdmin,
    WinAdmin,
    WinAdminForm,
    WinAdviserAdmin,
    WinSoftDeletedAdminForm,
)
from datahub.export_win.models import DeletedWin, Win, WinAdviser
from datahub.export_win.tasks import (
    notify_export_win_email_by_rq_email,
    send_export_win_email_notification_via_rq,
    update_customer_response_token_for_email_notification_id,
)
from datahub.export_win.test.factories import (
    CustomerResponseFactory,
    WinAdviserFactory,
    WinFactory,
)
from datahub.notification.constants import NotifyServiceName


@pytest.fixture
def win():
    return WinFactory()


@pytest.fixture
def customer_response(win: WinFactory):
    return CustomerResponseFactory(name='Test Customer Response', win_id=win.id)


@pytest.fixture
def admin():
    return WinAdmin(model=Win, admin_site=AdminSite())


@pytest.mark.django_db
def test_get_actions():
    """Test for actions."""
    user = AdviserFactory()
    admin = WinAdmin(Win, AdminSite())
    request_factory = RequestFactory()
    request = request_factory.get('/')
    request.user = user
    actions = admin.get_actions(request)
    assert 'delete_selected' not in actions


@pytest.mark.django_db
def test_soft_delete():
    """Test soft delete."""
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
    """Test undelete."""
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
    """Test for get softdeleted queryset."""
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
def test_get_company(admin):
    """Test for get company."""
    company = CompanyFactory()
    obj = WinFactory(company=company)
    result = admin.get_company(obj)

    assert result == company


@pytest.mark.django_db
def test_get_adviser(admin):
    """Test for get adviser."""
    adviser = AdviserFactory()
    obj = WinFactory(adviser=adviser)
    result = admin.get_adviser(obj)

    expected_result = f'{adviser} <{adviser.email}>'
    assert result == expected_result


@pytest.mark.django_db
def test_get_date_confirmed(admin):
    """Test for get date confirmed."""
    win = WinFactory()
    CustomerResponseFactory(responded_on='2024-04-01', win=win)
    result = admin.get_date_confirmed(win)

    expected_result = '2024-04-01'
    assert result == expected_result


@pytest.mark.django_db
def test_get_contact_names(admin):
    """Test for get contact names."""
    contact1 = ContactFactory(first_name='John', last_name='Doe')
    contact2 = ContactFactory(first_name='Jane', last_name='Smith')
    obj = WinFactory()
    obj.company_contacts.add(contact1, contact2)

    result = admin.get_contact_names(obj)

    expected_result = 'John Doe, Jane Smith'
    assert result == expected_result


@pytest.mark.django_db
def test_has_view_permission(admin):
    """Test for has view permission in deleted win."""
    regular_user = AdviserFactory()
    export_win_admin_group = Group.objects.create(name='ExportWinAdmin')
    regular_user.groups.add(export_win_admin_group)

    superuser = AdviserFactory(is_superuser=True)
    request = RequestFactory().get('/')

    request.user = regular_user
    assert admin.has_view_permission(request) is True

    request.user = AdviserFactory()
    assert admin.has_view_permission(request) is False

    request.user = superuser
    assert admin.has_view_permission(request) is True


@pytest.mark.django_db
def test_has_view_permission_for_anonymous_wins(admin):
    """Test for has view permission for anonymous wins."""
    regular_user = AdviserFactory()
    export_win_admin_group = Group.objects.create(name='ExportWinAdmin')
    regular_user.groups.add(export_win_admin_group)

    superuser = AdviserFactory(is_superuser=True)
    request = RequestFactory().get('/anonymouswin/')

    request.user = regular_user
    assert admin.has_view_permission(request) is True

    request.user = AdviserFactory()
    assert admin.has_view_permission(request) is False

    request.user = superuser
    assert admin.has_view_permission(request) is True


@pytest.mark.django_db
def test_get_queryset():
    """Test to get winadviser
    And only show winadviser where win is not deleted.
    """
    deleted_win1 = WinFactory(is_deleted=False)
    deleted_win2 = WinFactory(is_deleted=True)
    win_adviser1 = WinAdviserFactory(win=deleted_win1)
    win_adviser2 = WinAdviserFactory(win=deleted_win2)

    win_adviser_admin = WinAdviserAdmin(model=WinAdviser, admin_site=AdminSite())
    queryset = win_adviser_admin.get_queryset(request=None)
    assert win_adviser1 in queryset
    assert win_adviser2 not in queryset


@pytest.mark.django_db
def test_get_computed_adviser_name_adviser():
    """Test for get adviser name."""
    adviser = AdviserFactory(first_name='John', last_name='Smith')
    win_adviser = WinAdviserFactory(adviser=adviser)
    admin_instance = WinAdviserAdmin(model=WinAdviser, admin_site=AdminSite())
    assert admin_instance.get_computed_adviser_name(win_adviser) == 'John Smith'


@pytest.mark.django_db
def test_get_computed_adviser_name_legacy_adviser():
    """Test for get legacy adviser name."""
    win_adviser = WinAdviserFactory(adviser=None, name='John Smith')
    admin_instance = WinAdviserAdmin(model=WinAdviser, admin_site=AdminSite())
    assert admin_instance.get_computed_adviser_name(win_adviser) == 'John Smith'


@pytest.fixture
def mock_job_scheduler(monkeypatch):
    mock_job_scheduler = Mock()
    monkeypatch.setattr(
        'datahub.export_win.tasks.job_scheduler',
        mock_job_scheduler,
    )
    return mock_job_scheduler


@pytest.mark.django_db
class TestWinSoftDeletedAdminForm:
    """Test for WinSoftDeletedAdminForm."""

    def test_init_method(self):
        form = WinSoftDeletedAdminForm()
        assert form is not None


@pytest.mark.django_db
class TestWinAdminForm:
    """Test for WinAdminForm."""

    def test_win_admin_form(self):
        form = WinAdminForm()
        assert form is not None

        assert form.fields['audit'].required is True

        legacy_fields = {
            'cdms_reference': 'Data Hub (Companies House) or CDMS reference number',
            'customer_email_address': 'Contact email',
            'customer_job_title': 'Job title',
            'line_manager_name': 'Line manager',
            'lead_officer_email_address': 'Lead officer email address',
            'other_official_email_address': 'Secondary email address',
        }

        for field_name, label in legacy_fields.items():
            assert form.fields[field_name].required is False
            assert form.fields[field_name].label == f'{label} (legacy)'


@pytest.mark.django_db
class TestAnonymousWinAdminForm:
    """Test for AnonymousWinAdminForm."""

    def test_anonymous_win_admin_form_with_mandatory_fields(self):
        form = AnonymousWinAdminForm()
        assert form is not None

        optional_legacy_fields = {
            'cdms_reference': 'Data Hub (Companies House) or CDMS reference number',
            'customer_email_address': 'Contact email',
            'customer_job_title': 'Job title',
            'line_manager_name': 'Line manager',
            'lead_officer_email_address': 'Lead officer email address',
            'other_official_email_address': 'Secondary email address',
        }

        for field_name, label in optional_legacy_fields.items():
            assert form.fields[field_name].required is False
            assert form.fields[field_name].label == f'{label} (legacy)'

        mandatory_fields_for_anonymous_wins = {
            'lead_officer': 'Lead officer',
            'export_experience': 'Export experience',
            'business_potential': 'Medium-sized and high potential companies',
            'customer_location': 'HQ location',
            'sector': 'Sector',
        }

        for field_name, label in mandatory_fields_for_anonymous_wins.items():
            assert form.fields[field_name].required is True
            assert form.fields[field_name].label == f'{label}'

    def notify_anonymous_wins_adviser_as_contact(
        self,
        mock_job_scheduler,
    ):
        """Test for notify anonymous wins adviser as contact.

        It should schedule a task to:
            * notify an adviser
            * trigger a second task to store the notification_id
        """
        adviser_email_address = 'win.admin@example.com'
        template_id = str(uuid.uuid4())
        context = {}
        token_id = uuid.uuid4()

        notify_export_win_email_by_rq_email(
            adviser_email_address,
            template_id,
            context,
            update_customer_response_token_for_email_notification_id,
            token_id,
        )
        mock_job_scheduler.assert_called_once_with(
            function=send_export_win_email_notification_via_rq,
            function_args=(
                adviser_email_address,
                template_id,
                context,
                update_customer_response_token_for_email_notification_id,
                token_id,
                NotifyServiceName.export_win,
            ),
            retry_backoff=True,
            max_retries=5,
        )

        mock_job_scheduler.reset_mock()
        notify_export_win_email_by_rq_email(
            adviser_email_address,
            template_id,
            context,
            update_customer_response_token_for_email_notification_id,
            token_id,
        )
        mock_job_scheduler.assert_called_once_with(
            function=send_export_win_email_notification_via_rq,
            function_args=(
                adviser_email_address,
                template_id,
                context,
                update_customer_response_token_for_email_notification_id,
                token_id,
                NotifyServiceName.export_win,
            ),
            retry_backoff=True,
            max_retries=5,
        )


@pytest.mark.django_db
class TestWinBreakdownInlineForm:
    """Test for Breakdown in line form."""

    def test_init_method(self):
        form = BreakdownInlineForm()
        assert form is not None


@pytest.mark.django_db
class TestAdvisorInlineForm:
    """Test for Adviser in line form."""

    def test_init_method(self):
        form = AdvisorInlineForm()
        assert form is not None


class InstanceMock:
    def __init__(self, pk):
        self.pk = pk

    @property
    def _meta(self):
        return type(
            'Meta',
            (),
            {
                'fields': [],
                'exclude': [],
                'concrete_fields': [],
                'private_fields': [],
                'many_to_many': [],
            },
        )


@pytest.mark.django_db
class TestCustomerResponseInlineForm:
    """Test for Customer Response in line form
    Field name is not required and field id should be read-only.
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
