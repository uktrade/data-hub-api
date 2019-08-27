from unittest import mock

import pytest

from datahub.email_ingestion.validation import was_email_sent_by_dit


@pytest.mark.parametrize(
    'email,authentication_results,expected_result',
    (
        # Valid trade.gov.uk email - authentication exempt
        (
            'bill.adama@trade.gov.uk',
            None,
            True,
        ),
        # Valid digital.trade.gov.uk email, ensure whitelist is case insensitive
        (
            'bill.Adama@digital.trade.gov.uk',
            '\n'.join([
                'mx.google.com;',
                'dkim=pass header.i=@digital.trade.gov.uk header.s=selector1 header.b=foobar;',
                'spf=pass (google.com: domain of bill.adama@digital.trade.gov.uk designates '
                'XX.XXX.XX.XX as permitted sender) smtp.mailfrom=bill.adama@digital.trade.gov.uk;',
                'dmarc=pass (p=QUARANTINE sp=QUARANTINE dis=NONE) '
                'header.from=digital.trade.gov.uk',
                'compauth=pass (reason=109)',
            ]),
            True,
        ),
        # Invalid domain - not on DIT adviser whitelist
        (
            'bill.adama@gmail.com',
            '\n'.join([
                'mx.google.com;',
                'dkim=pass header.i=@gmail.com header.s=selector1 header.b=foobar;',
                'spf=pass (google.com: domain of bill.adama@gmail.com designates '
                'XX.XXX.XX.XX as permitted sender) smtp.mailfrom=bill.adama@gmail.com;',
                'dmarc=pass (p=QUARANTINE sp=QUARANTINE dis=NONE) header.from=gmail.com',
                'compauth=pass (reason=109)',
            ]),
            # TODO: Will need review as we adjust domain verification during trial
            False,
        ),
        # Invalid authentication results - dkim
        (
            'bill.adama@digital.trade.gov.uk',
            '\n'.join([
                'mx.google.com;',
                'dkim=fail header.i=@digital.trade.gov.uk header.s=selector1 header.b=foobar;',
                'spf=pass (google.com: domain of bill.adama@digital.trade.gov.uk designates '
                'XX.XXX.XX.XX as permitted sender) smtp.mailfrom=bill.adama@digital.trade.gov.uk;',
                (
                    'dmarc=pass (p=QUARANTINE sp=QUARANTINE dis=NONE) '
                    'header.from=digital.trade.gov.uk'
                ),
                'compauth=pass (reason=109)',
            ]),
            False,
        ),
        # Invalid authentication results - spf
        (
            'bill.adama@digital.trade.gov.uk',
            '\n'.join([
                'mx.google.com;',
                'dkim=pass header.i=@digital.trade.gov.uk header.s=selector1 header.b=foobar;',
                'spf=fail (google.com: domain of bill.adama@digital.trade.gov.uk designates '
                'XX.XXX.XX.XX as permitted sender) smtp.mailfrom=bill.adama@digital.trade.gov.uk;',
                (
                    'dmarc=pass (p=QUARANTINE sp=QUARANTINE dis=NONE) '
                    'header.from=digital.trade.gov.uk'
                ),
                'compauth=pass (reason=109)',
            ]),
            False,
        ),
        # Invalid authentication results - dmarc
        (
            'bill.adama@digital.trade.gov.uk',
            '\n'.join([
                'mx.google.com;',
                'dkim=pass header.i=@digital.trade.gov.uk header.s=selector1 header.b=foobar;',
                'spf=pass (google.com: domain of bill.adama@digital.trade.gov.uk designates ',
                'XX.XXX.XX.XX as permitted sender) smtp.mailfrom=bill.adama@digital.trade.gov.uk;',
                (
                    'dmarc=fail (p=QUARANTINE sp=QUARANTINE dis=NONE) '
                    'header.from=digital.trade.gov.uk'
                ),
                'compauth=pass (reason=109)',
            ]),
            False,
        ),
        # Missing authentication results for spf
        (
            'bill.adama@digital.trade.gov.uk',
            '\n'.join([
                'mx.google.com;',
                'dkim=pass header.i=@digital.trade.gov.uk header.s=selector1 header.b=foobar;',
                (
                    'dmarc=pass (p=QUARANTINE sp=QUARANTINE dis=NONE) '
                    'header.from=digital.trade.gov.uk'
                ),
                'compauth=pass (reason=109)',
            ]),
            False,
        ),
        # Extra unknown auth method - still passes
        (
            'bill.adama@digital.trade.gov.uk',
            '\n'.join([
                'mx.google.com;',
                'dkim=pass header.i=@digital.trade.gov.uk header.s=selector1 header.b=foobar;',
                'spf=pass (google.com: domain of bill.adama@digital.trade.gov.uk designates '
                'XX.XXX.XX.XX as permitted sender) smtp.mailfrom=bill.adama@digital.trade.gov.uk;',
                'dmarc=pass (p=QUARANTINE sp=QUARANTINE dis=NONE) '
                'header.from=digital.trade.gov.uk;',
                'sender-id=fail header.from=example.com',
                'compauth=pass (reason=109)',
            ]),
            True,
        ),
        # Domain with no auth methods set, uses default methods and fails
        (
            'bill.adama@other.trade.gov.uk',
            '\n'.join([
                'mx.google.com;',
                'dkim=fail header.i=@digital.trade.gov.uk header.s=selector1 header.b=foobar;',
                'spf=fail (google.com: domain of bill.adama@digital.trade.gov.uk designates '
                'XX.XXX.XX.XX as permitted sender) smtp.mailfrom=bill.adama@digital.trade.gov.uk;',
                'dmarc=pass (p=QUARANTINE sp=QUARANTINE dis=NONE) '
                'header.from=digital.trade.gov.uk;',
                'compauth=pass (reason=109)',
            ]),
            False,
        ),
        # Blacklisted email
        (
            'blacklisted@trade.gov.uk',
            None,
            False,
        ),
    ),
)
def test_email_sent_by_dit(email, authentication_results, expected_result):
    """
    Tests for was_email_sent_by_dit validator.
    """
    message = mock.Mock()
    message.from_ = [['Bill Adama', email]]
    message.authentication_results = authentication_results
    result = was_email_sent_by_dit(message)
    assert result == expected_result


def test_bad_from_returns_false():
    """
    Test was_email_sent_by_dit validator when the from_ attribute is malformed.
    """
    message = mock.Mock()
    # This should be an iterable of pairs - simulate a malformed from attribute
    message.from_ = []
    result = was_email_sent_by_dit(message)
    assert result is False
