import pytest
from django.contrib.admin.sites import site as admin_site
from django.test import RequestFactory

from datahub.company.test.factories import AdviserFactory
from datahub.export_win.admin import DeletedWinAdmin, WinAdmin
from datahub.export_win.models import DeletedWin, Win
from datahub.export_win.test.factories import DeletedWinFactory


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
    """Return adviser as user with email."""
    user = AdviserFactory()
    win1 = DeletedWinFactory()
    win2 = DeletedWinFactory()
    admin = WinAdmin(Win, None)
    request = RequestFactory().get('/')
    request.user = user
    queryset = Win.objects.filter(pk__in=[win1.pk, win2.pk])
    admin.soft_delete(request, queryset)
    win1.refresh_from_db()
    win2.refresh_from_db()
    assert win1.is_deleted
    assert win2.is_deleted


@pytest.mark.django_db
def test_reinstate():
    user = AdviserFactory()

    deleted_win1 = DeletedWinFactory()
    deleted_win2 = DeletedWinFactory()
    deleted_win1.is_deleted = True
    deleted_win2.is_deleted = True

    request_factory = RequestFactory()
    request = request_factory.get('/')
    request.user = user

    admin = DeletedWinAdmin(model=DeletedWin, admin_site=None)

    admin.reinstate(request, queryset=DeletedWin.objects.all())

    deleted_win1.refresh_from_db()
    deleted_win2.refresh_from_db()

    assert not deleted_win1.is_deleted
    assert not deleted_win2.is_deleted
