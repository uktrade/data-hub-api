import subprocess
from unittest.mock import Mock

import pytest

from script_utils.git import (
    any_uncommitted_changes,
    get_file_contents,
    local_branch_exists,
    remote_branch_exists,
    remote_tag_exists,
)


@pytest.fixture
def mock_subprocess_run(monkeypatch):
    """Patch subprocess.run()."""
    run_mock = Mock()
    monkeypatch.setattr(subprocess, 'run', run_mock)
    yield run_mock


@pytest.mark.parametrize(
    'stdout,expected_result',
    [
        (' M scripts/create_changelog.py\n', True),
        ('', False),
    ],
)
def test_any_uncommitted_changes(stdout, expected_result, mock_subprocess_run):
    """Test that any_uncommitted_changes() returns the expected value in various scenarios."""
    mock_subprocess_run.return_value = subprocess.CompletedProcess((), 0, stdout=stdout)

    assert any_uncommitted_changes() == expected_result


def test_get_file_contents(mock_subprocess_run):
    """Test that get_file_contents() returns the contents of stdout."""
    mock_subprocess_run.return_value = subprocess.CompletedProcess((), 0, stdout=b'file-contents')

    assert get_file_contents('origin/master', 'file.txt') == 'file-contents'


@pytest.mark.parametrize(
    'side_effect,expected_result',
    [
        (None, True),
        (subprocess.CalledProcessError(1, ''), False),
    ],
)
def test_local_branch_exists(side_effect, expected_result, mock_subprocess_run):
    """Test that local_branch_exists() returns the expected value in various scenarios."""
    mock_subprocess_run.side_effect = side_effect

    assert local_branch_exists('test-branch') == expected_result


@pytest.mark.parametrize(
    'side_effect,expected_result',
    [
        (None, True),
        (subprocess.CalledProcessError(2, ''), False),
    ],
)
def test_remote_branch_exists(side_effect, expected_result, mock_subprocess_run):
    """Test that remote_branch_exists() returns the expected value in various scenarios."""
    mock_subprocess_run.side_effect = side_effect

    assert remote_branch_exists('test-branch') == expected_result


@pytest.mark.parametrize(
    'side_effect,expected_result',
    [
        (None, True),
        (subprocess.CalledProcessError(2, ''), False),
    ],
)
def test_remote_tag_exists(side_effect, expected_result, mock_subprocess_run):
    """Test that remote_tag_exists() returns the expected value in various scenarios."""
    mock_subprocess_run.side_effect = side_effect

    assert remote_tag_exists('test-tag') == expected_result
