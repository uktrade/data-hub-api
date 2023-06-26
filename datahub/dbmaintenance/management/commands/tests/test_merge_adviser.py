import pytest

from django.core.management import call_command

from datahub.company.models import Advisor
from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import APITestMixin


class TestAdviser(APITestMixin):
    def test_invalid_advisor_id(self):
        """Test with non-existent advisor id."""
        active_advisor = AdviserFactory(is_active=True)
        with pytest.raises(Advisor.DoesNotExist):
            call_command(
                'merge_adviser',
                '12345678-1234-5678-1234-567812345678',
                str(active_advisor.id),
            )

    def test_invalid_active_advisor_id(self):
        """Test with non-existent advisor id."""
        inactive_advisor = AdviserFactory(is_active=False)
        with pytest.raises(Advisor.DoesNotExist):
            call_command(
                'merge_adviser',
                str(inactive_advisor.id),
                '12345678-1234-5678-1234-567812345678',
            )

    def test_merge_adviser_output(self, capfd):
        """Test the stdout and stderr of the command."""
        active_advisor = AdviserFactory(is_active=True)
        inactive_advisor = AdviserFactory(is_active=False)
        call_command('merge_adviser', str(inactive_advisor.id), str(active_advisor.id))

        out, err = capfd.readouterr()
        assert 'Successfully deleted inactive advisor' in out
        assert err == ''
