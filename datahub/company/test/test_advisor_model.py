from unittest import mock

from datahub.company.models import Advisor
from datahub.core.test_utils import LeelooTestCase


class TestAdvisorModel(LeelooTestCase):
    """Advisor model test case."""

    @mock.patch('datahub.core.mixins.DeferredSaveModelMixin.save')
    def test_save_sets_email_as_login_if_empty(self, save_mock):
        """Should set username to email when empty."""
        advisor = Advisor(first_name='test', last_name='test',
                          email='test@example.com')

        advisor.save()

        self.assertEqual(advisor.username, advisor.email)
        self.assertTrue(save_mock.called)

    @mock.patch('datahub.core.mixins.DeferredSaveModelMixin.save')
    def test_save_does_not_override_correct_username(self, save_mock):
        """Should leave username untouched."""
        advisor = Advisor(first_name='test', last_name='test',
                          username='tester', email='test@example.com')

        advisor.save()

        self.assertEqual(advisor.username, 'tester')
        self.assertEqual(advisor.email, 'test@example.com')
        self.assertTrue(save_mock.called)
