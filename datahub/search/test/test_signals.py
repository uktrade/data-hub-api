from unittest.mock import Mock

import pytest

from datahub.search.apps import get_search_apps
from datahub.search.signals import disable_search_signal_receivers
from datahub.search.test.search_support.models import RelatedModel, SimpleModel


@pytest.mark.django_db
class TestDisableSignalsForModel:
    """Tests for disable_search_signal_receivers()."""

    def test_signal_receivers_are_not_disabled(self, setup_es, monkeypatch):
        """
        Test that signal receivers are active without the context manager being active.
        """
        callback_mock = Mock()
        monkeypatch.setattr(
            'datahub.search.test.search_support.relatedmodel.signals._dummy_callback',
            callback_mock,
        )

        SimpleModel().save()

        callback_mock.assert_called_once()

    def test_signal_receivers_disabled_for_model(self, setup_es, monkeypatch):
        """
        Test that signal receivers are disabled for the specified model.

        Note: Model refers to the signal sender, not the search app model. Hence while signal
        receivers are disabled for SimpleModel, it is the relatedmodel app signal receivers that
        are checked.
        """
        callback_mock = Mock()
        monkeypatch.setattr(
            'datahub.search.test.search_support.relatedmodel.signals._dummy_callback',
            callback_mock,
        )

        with disable_search_signal_receivers(SimpleModel):
            SimpleModel().save()

        callback_mock.assert_not_called()

    def test_does_not_affect_other_models(self, setup_es, monkeypatch):
        """Test that signal receivers are not disabled for other models."""
        callback_mock = Mock()
        monkeypatch.setattr(
            'datahub.search.test.search_support.relatedmodel.signals._dummy_callback',
            callback_mock,
        )

        with disable_search_signal_receivers(SimpleModel):
            RelatedModel().save()

        callback_mock.assert_called_once()

    def test_reconnects_if_was_connected(self, setup_es):
        """Test that signal receivers are reconnected on context manager exit."""
        with disable_search_signal_receivers(SimpleModel):
            pass

        assert all(
            receiver.is_connected
            for search_app in get_search_apps()
            for receiver in search_app.get_signals_receivers()
            if receiver.sender is SimpleModel
        )

    def test_reconnects_if_exception_raised(self, setup_es):
        """
        Test that signal receivers are reconnected if an exception is raised while the
        context manager is active.
        """
        try:
            with disable_search_signal_receivers(SimpleModel):
                raise ValueError
        except ValueError:
            pass

        assert all(
            receiver.is_connected
            for search_app in get_search_apps()
            for receiver in search_app.get_signals_receivers()
            if receiver.sender is SimpleModel
        )

    def test_does_not_reconnect_if_was_disconnected(self):
        """
        Test that signal receivers are not reconnected when not originally connected.

        Note: Signal receivers are not connected as the setup_es fixture is not used.
        """
        with disable_search_signal_receivers(SimpleModel):
            pass

        assert not any(
            receiver.is_connected
            for search_app in get_search_apps()
            for receiver in search_app.get_signals_receivers()
            if receiver.sender is SimpleModel
        )
