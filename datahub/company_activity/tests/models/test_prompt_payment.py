from datetime import date

import pytest
from django.db import IntegrityError

from datahub.company_activity.models import PromptPayments
from datahub.company_activity.tests.factories import PromptPaymentsFactory

pytestmark = pytest.mark.django_db


class TestPromptPaymentModel:
    """Tests for the PromptPayment model."""

    def test_str_representation(self):
        """Test the string representation of the model."""
        prompt_payment = PromptPaymentsFactory(
            company_name='Test Corp',
            company_house_number='12345678',
            reporting_period_start_date='2025-01-01',
            reporting_period_end_date=date(2025, 3, 31),  # chaining lazy evals
        )
        expected_str = 'Test Corp (12345678) - 2025-01-01 to 2025-03-31'
        assert str(prompt_payment) == expected_str

    def test_unique_source_id_constraint(self):
        """Test that source_id must be unique."""
        PromptPaymentsFactory(source_id=123)
        with pytest.raises(IntegrityError):
            PromptPaymentsFactory(source_id=123)

    def test_nullable_company_fk(self):
        """Test that the company foreign key can be null."""
        prompt_payment = PromptPaymentsFactory(company=None)
        assert prompt_payment.company is None
        retrieved = PromptPayments.objects.get(pk=prompt_payment.pk)
        assert retrieved.company is None

    def test_nullable_contact_fk(self):
        """Test that the contact foreign key can be null."""
        prompt_payment = PromptPaymentsFactory(contact=None)
        assert prompt_payment.contact is None
        retrieved = PromptPayments.objects.get(pk=prompt_payment.pk)
        assert retrieved.contact is None

    def test_default_ordering(self):
        """Test the default ordering of the model."""
        pp1 = PromptPaymentsFactory(
            filing_date='2025-01-15',
            reporting_period_end_date='2024-12-31',
        )
        pp2 = PromptPaymentsFactory(
            filing_date='2025-03-10',
            reporting_period_end_date='2025-02-28',
        )
        pp3 = PromptPaymentsFactory(
            filing_date='2025-03-10',
            reporting_period_end_date='2025-01-31',
        )
        pp4 = PromptPaymentsFactory(
            filing_date='2024-12-20',
            reporting_period_end_date='2024-11-30',
        )

        results = list(PromptPayments.objects.all())
        assert results == [pp2, pp3, pp1, pp4]
