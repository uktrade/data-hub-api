import pytest
from django.test import RequestFactory

from datahub.company.test.factories import AdviserFactory
from datahub.export_win.admin import DeletedWinAdmin
from datahub.export_win.models import DeletedWin
from datahub.export_win.test.factories import DeletedWinFactory


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
