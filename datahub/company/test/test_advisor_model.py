from unittest import mock

from datahub.company.models import Advisor


@mock.patch('datahub.core.mixins.DeferredSaveModelMixin.save')
def test_save_sets_email_as_login_if_empty(save_mock):
    """Should set username to email when empty."""
    advisor = Advisor(first_name='test', last_name='test',
                      email='test@example.com')

    advisor.save()

    assert advisor.username == advisor.email
    assert save_mock.called


@mock.patch('datahub.core.mixins.DeferredSaveModelMixin.save')
def test_save_does_not_override_correct_username(save_mock):
    """Should leave username untouched."""
    advisor = Advisor(first_name='test', last_name='test',
                      username='tester', email='test@example.com')

    advisor.save()

    assert advisor.username == 'tester'
    assert advisor.email == 'test@example.com'
    assert save_mock.called
