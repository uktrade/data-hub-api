"""Tests for investment models."""

import pytest

from datahub.investment.proposition.test.factories import PropositionFactory

pytestmark = pytest.mark.django_db


def test_proposition():
    """Tests that proposition can be created."""
    PropositionFactory()
