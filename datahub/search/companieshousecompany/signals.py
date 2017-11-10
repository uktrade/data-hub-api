"""
Signals for companieshousecompany are not connected, because the data will only
change via sync_ch command. After syncing Companies House data, sync_es command
should be issued to sync db with Elasticsearch.
"""


def connect_signals():
    """Connect signals for ES sync."""
    pass


def disconnect_signals():
    """Disconnect signals from ES sync."""
    pass
