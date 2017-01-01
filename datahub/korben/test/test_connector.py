from datahub.korben.connector import KorbenConnector


def test_handle_host():
    """Test handle host."""
    connector = KorbenConnector('foo')
    assert connector.handle_host() == 'http://foo'


def test_handle_host_with_protocol():
    """Test handle host with protocol."""
    connector = KorbenConnector('https://foo')
    assert connector.handle_host() == 'https://foo'
