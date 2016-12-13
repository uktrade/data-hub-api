from django.db.migrations.loader import MigrationLoader


def test_no_conflicting_migrations():
    """Test that there are no conflicting migrations."""
    loader = MigrationLoader(None, ignore_no_migrations=True)
    conflicts = loader.detect_conflicts()
    assert not conflicts, 'Conflicting migrations detected.'
