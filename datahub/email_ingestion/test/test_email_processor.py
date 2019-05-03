import pytest

from datahub.email_ingestion.email_processor import EmailProcessor


def test_email_processor_not_implemented():
    """
    Test that the EmailProcessor base class will raise an appropriate error when
    it has been incorrectly subclassed.
    """
    class BadEmailProcessor(EmailProcessor):
        pass
    with pytest.raises(TypeError):
        BadEmailProcessor()
