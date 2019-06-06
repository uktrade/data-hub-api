from unittest import mock


MAILBOXES_SETTING = {
    'mybox1': {
        'username': 'mybox1@example.net',
        'password': 'foobarbaz1',
        'imap_domain': 'imap.example.net',
        'processor_classes': [
            'datahub.email_ingestion.processor_1.Processor',
            'datahub.email_ingestion.processor_2.Processor',
        ],
    },
    'mybox2': {
        'username': 'mybox2@example.net',
        'password': 'foobarbaz2',
        'imap_domain': 'imap.example.net',
        'processor_classes': [
            'datahub.email_ingestion.processor_1.Processor',
            'datahub.email_ingestion.processor_2.Processor',
        ],
    },
}

# Mailbox missing password configuration
BAD_MAILBOXES_SETTING = {
    'mybox1': {
        'username': 'mybox1@example.net',
        'imap_domain': 'imap.example.net',
        'processor_classes': [
            'datahub.email_ingestion.processor_1.Processor',
            'datahub.email_ingestion.processor_2.Processor',
        ],
    },
}


def mock_import_string(monkeypatch):
    """
    Mock import_string the import_string function in the
    datahub.email_ingestion.mailbox module.
    """
    import_string_mock = mock.Mock()
    monkeypatch.setattr(
        'datahub.email_ingestion.mailbox.import_string',
        import_string_mock,
    )
    return import_string_mock
