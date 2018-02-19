import pytest

from ..govukpay import govuk_url, GOVUKPayAPIException, PayClient


def test_govuk_url(settings):
    """
    Test that the url to a GOV.UK endpoint is built from the value base
    in the django settings.
    """
    settings.GOVUK_PAY_URL = 'http://test.example.com/'

    assert govuk_url('test-path') == 'http://test.example.com/test-path'


class TestPayClientCreatePayment:
    """Tests related to the create payment method."""

    def test_ok(self, requests_stubber):
        """Test a successful call to the GOV.UK create payment endpoint."""
        # mock response
        json_response = {
            'state': {'status': 'created', 'finished': False},
            'payment_id': '123abc123abc123abc123abc12',
            '_links': {
                'next_url': {
                    'href': 'https://payment.example.com/123abc',
                    'method': 'GET'
                },
            }
        }
        url = govuk_url('payments')
        requests_stubber.post(url, status_code=201, json=json_response)

        # make API call
        pay = PayClient()
        response = pay.create_payment(
            amount=1234,
            reference='payment reference',
            description='payment description',
            return_url='http://return.example.com'
        )

        # check response
        assert response == json_response

        # check the mocked object
        assert requests_stubber.call_count == 1
        assert requests_stubber.request_history[-1].url == url
        assert requests_stubber.request_history[-1].json() == {
            'amount': 1234,
            'reference': 'payment reference',
            'description': 'payment description',
            'return_url': 'http://return.example.com'
        }

    @pytest.mark.parametrize(
        'status_code,error_msg',
        (
            (400, '400 Client Error'),
            (401, '401 Client Error'),
            (404, '404 Client Error'),
            (409, '409 Client Error'),
            (500, '500 Server Error')
        )
    )
    def test_http_error(self, status_code, error_msg, requests_stubber):
        """Test that if GOV.UK Pay returns an HTTP error, an exception is raised."""
        url = govuk_url('payments')
        requests_stubber.post(url, status_code=status_code, reason=error_msg)

        with pytest.raises(GOVUKPayAPIException) as exc:
            pay = PayClient()
            pay.create_payment(
                amount=1234,
                reference='payment reference',
                description='payment description',
                return_url='http://return.example.com'
            )
        assert exc.value.detail == f'{error_msg}: {error_msg} for url: {url}'


class TestPayClientGetPaymentById:
    """Tests related to the get payment by id method."""

    def test_ok(self, requests_stubber):
        """Test a successful call to get a GOV.UK payment."""
        # mock response
        payment_id = '123abc123abc123abc123abc12'
        json_response = {
            'state': {'status': 'started', 'finished': False},
            'payment_id': payment_id,
            '_links': {
                'next_url': {
                    'href': 'https://payment.example.com/123abc',
                    'method': 'GET'
                },
            }
        }
        url = govuk_url(f'payments/{payment_id}')
        requests_stubber.get(url, status_code=200, json=json_response)

        # make API call
        pay = PayClient()
        response = pay.get_payment_by_id(payment_id)

        # check
        assert response == json_response
        assert requests_stubber.call_count == 1
        assert requests_stubber.request_history[-1].url == url

    @pytest.mark.parametrize(
        'status_code,error_msg',
        (
            (401, '401 Client Error'),
            (404, '404 Client Error'),
            (500, '500 Server Error')
        )
    )
    def test_http_error(self, status_code, error_msg, requests_stubber):
        """Test that if GOV.UK Pay returns an HTTP error, an exception is raised."""
        payment_id = '123abc123abc123abc123abc12'
        url = govuk_url(f'payments/{payment_id}')
        requests_stubber.get(url, status_code=status_code, reason=error_msg)

        with pytest.raises(GOVUKPayAPIException) as exc:
            pay = PayClient()
            pay.get_payment_by_id(payment_id)
        assert exc.value.detail == f'{error_msg}: {error_msg} for url: {url}'


class TestPayClientCancelPayment:
    """Tests related to the cancel payment method."""

    def test_ok(self, requests_stubber):
        """Test a successful call to cancel a GOV.UK payment."""
        # mock response
        payment_id = '123abc123abc123abc123abc12'
        url = govuk_url(f'payments/{payment_id}/cancel')
        requests_stubber.post(url, status_code=204)

        # make API call
        pay = PayClient()
        pay.cancel_payment(payment_id)

        # check
        assert requests_stubber.call_count == 1
        assert requests_stubber.request_history[-1].url == url

    @pytest.mark.parametrize(
        'status_code,error_msg',
        (
            (400, '400 Client Error'),
            (401, '401 Client Error'),
            (404, '404 Client Error'),
            (409, '409 Client Error'),
            (500, '500 Server Error')
        )
    )
    def test_http_error(self, status_code, error_msg, requests_stubber):
        """Test that if GOV.UK Pay returns an HTTP error, an exception is raised."""
        payment_id = '123abc123abc123abc123abc12'
        url = govuk_url(f'payments/{payment_id}/cancel')
        requests_stubber.post(url, status_code=status_code, reason=error_msg)

        with pytest.raises(GOVUKPayAPIException) as exc:
            pay = PayClient()
            pay.cancel_payment(payment_id)
        assert exc.value.detail == f'{error_msg}: {error_msg} for url: {url}'
