import logging
from unittest import mock

import pytest

from datahub.email_ingestion.validation import was_email_sent_by_dit


@pytest.mark.parametrize(
    'email,authentication_results,expected_result,expected_warning',
    (
        # Valid trade.gov.uk email - authentication exempt
        (
            'bill.adama@trade.gov.uk',
            None,
            True,
            None,
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
            None,
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
            None,
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
            None,
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
            None,
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
            None,
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
            None,
        ),
        # Domain which is not on DIT_EMAIL_DOMAINS setting, fails validation
        (
            'bill.adama@other.trade.gov.uk',
            '\n'.join([
                'mx.google.com;',
                'dkim=pass header.i=@digital.trade.gov.uk header.s=selector1 header.b=foobar;',
                'spf=pass (google.com: domain of bill.adama@digital.trade.gov.uk designates '
                'XX.XXX.XX.XX as permitted sender) smtp.mailfrom=bill.adama@digital.trade.gov.uk;',
                'dmarc=pass (p=QUARANTINE sp=QUARANTINE dis=NONE) '
                'header.from=digital.trade.gov.uk;',
                'compauth=pass (reason=109)',
            ]),
            False,
            (
                'Domain "other.trade.gov.uk" not present in DIT_EMAIL_DOMAINS setting. '
                'This email had the following authentication results: compauth=pass dkim=pass '
                'dmarc=pass spf=pass'
            ),
        ),
        # Domain which is not on DIT_EMAIL_DOMAINS setting, fails validation
        (
            'joe.bloggs@gmail.com',
            '\n'.join([
                'mx.google.com;',
                'dkim=pass header.i=@gmail.com header.s=selector1 header.b=foobar;',
                'spf=pass (google.com: domain of joe.bloggs@gmail.com designates '
                'XX.XXX.XX.XX as permitted sender) smtp.mailfrom=bill.adama@digital.trade.gov.uk;',
                'dmarc=pass (p=QUARANTINE sp=QUARANTINE dis=NONE) '
                'header.from=digital.trade.gov.uk;',
            ]),
            False,
            (
                'Domain "gmail.com" not present in DIT_EMAIL_DOMAINS setting. '
                'This email had the following authentication results: dkim=pass '
                'dmarc=pass spf=pass'
            ),
        ),
        # Blacklisted email
        (
            'blacklisted@trade.gov.uk',
            None,
            False,
            None,
        ),
    ),
)
def test_email_sent_by_dit(
    caplog,
    email,
    authentication_results,
    expected_result,
    expected_warning,
):
    """
    Tests for was_email_sent_by_dit validator.
    """
    caplog.set_level(logging.WARNING)
    message = mock.Mock()
    message.from_ = [['Bill Adama', email]]
    message.authentication_results = authentication_results
    result = was_email_sent_by_dit(message)
    assert result == expected_result
    if expected_warning:
        expected_log = (
            'datahub.email_ingestion.validation',
            30,
            expected_warning,
        )
        assert expected_log in caplog.record_tuples


def test_bad_from_returns_false():
    """
    Test was_email_sent_by_dit validator when the from_ attribute is malformed.
    """
    message = mock.Mock()
    # This should be an iterable of pairs - simulate a malformed from attribute
    message.from_ = []
    result = was_email_sent_by_dit(message)
    assert result is False
