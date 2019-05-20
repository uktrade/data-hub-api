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
        # Valid digital.trade.gov.uk email
        (
            'bill.adama@digital.trade.gov.uk',
            '\n'.join([
                'mx.google.com;',
                'dkim=pass header.i=@digital.trade.gov.uk header.s=selector1 header.b=foobar;',
                'spf=pass (google.com: domain of bill.adama@digital.trade.gov.uk designates '
                'XX.XXX.XX.XX as permitted sender) smtp.mailfrom=bill.adama@digital.trade.gov.uk;',
                'dmarc=pass (p=QUARANTINE sp=QUARANTINE dis=NONE) '
                'header.from=digital.trade.gov.uk',
            ]),
            True,
        ),
        # Invalid domain
        (
            'bill.adama@gmail.com',
            '\n'.join([
                'mx.google.com;',
                'dkim=pass header.i=@gmail.com header.s=selector1 header.b=foobar;',
                'spf=pass (google.com: domain of bill.adama@gmail.com designates '
                'XX.XXX.XX.XX as permitted sender) smtp.mailfrom=bill.adama@gmail.com;',
                'dmarc=pass (p=QUARANTINE sp=QUARANTINE dis=NONE) header.from=gmail.com',
            ]),
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
            ]),
            False,
        ),
        # Invalid authentication results - email mismatch
        (
            'bill.adama@digital.trade.gov.uk',
            '\n'.join([
                'mx.google.com;',
                'dkim=pass header.i=@digital.trade.gov.uk header.s=selector1 header.b=foobar;',
                'spf=pass (google.com: domain of bill.adama@digital.trade.gov.uk designates ',
                'XX.XXX.XX.XX as permitted sender) smtp.mailfrom=foobar@digital.trade.gov.uk;',
                (
                    'dmarc=pass (p=QUARANTINE sp=QUARANTINE dis=NONE) '
                    'header.from=digital.trade.gov.uk'
                ),
            ]),
            False,
        ),
    ),
)
def test_email_sent_by_dit(email, authentication_results, expected_result):
    """
    Tests for email_sent_by_dit validator.
    """
    message = mock.Mock()
    message.from_ = [['Bill Adama', email]]
    message.authentication_results = authentication_results
    result = was_email_sent_by_dit(message)
    assert result == expected_result
