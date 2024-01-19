import uuid
from datetime import date, datetime, timedelta

from unittest import mock

import pytest
import pytz
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import (Sum)

from freezegun import freeze_time

from datahub.company.test.factories import ContactFactory
from datahub.export_win.models import Breakdown, CustomerResponseToken
from datahub.export_win.tasks import (
    create_token_for_contact,
    get_all_fields_for_client_email_receipt,
    get_all_fields_for_lead_officer_email_receipt_no,
    get_all_fields_for_lead_officer_email_receipt_yes,
    notify_export_win_contact_by_rq_email,
    send_export_win_email_notification_via_rq,
    update_customer_response_token_for_email_notification_id,
    update_notify_email_delivery_status_for_customer_response_token,
)
from datahub.export_win.test.factories import (
    BreakdownFactory, CustomerResponseFactory, CustomerResponseTokenFactory,
)
from datahub.notification.constants import NotifyServiceName
from datahub.reminder.models import EmailDeliveryStatus

pytestmark = pytest.mark.django_db


@pytest.fixture()
def mock_export_win_tasks_notify_gateway(monkeypatch):
    mock_notify_gateway = mock.Mock()
    monkeypatch.setattr(
        'datahub.export_win.tasks.notify_gateway',
        mock_notify_gateway,
    )
    return mock_notify_gateway


@pytest.fixture()
def mock_job_scheduler(monkeypatch):
    mock_job_scheduler = mock.Mock()
    monkeypatch.setattr(
        'datahub.export_win.tasks.job_scheduler',
        mock_job_scheduler,
    )
    return mock_job_scheduler


@pytest.fixture()
def mock_update_customer_response_token_for_email_notification_id(monkeypatch):
    mock_update_customer_response_token_for_email_notification_id = mock.Mock()
    monkeypatch.setattr(
        'datahub.export_win.tasks.update_customer_response_token_for_email_notification_id',
        mock_update_customer_response_token_for_email_notification_id,
    )
    return mock_update_customer_response_token_for_email_notification_id


@pytest.fixture()
def mock_update_notify_email_delivery_status_for_customer_response_token(monkeypatch):
    mock_update_notify_email_delivery_status_for_customer_response_token = mock.Mock()
    monkeypatch.setattr(
        'datahub.export_win.tasks.update_notify_email_delivery_status_for_customer_response_token',
        mock_update_notify_email_delivery_status_for_customer_response_token,
    )
    return mock_update_notify_email_delivery_status_for_customer_response_token


@pytest.mark.django_db
@freeze_time('2023-07-01T10:00:00')
class TestUpdateEmailDeliveryStatusTask:
    current_date = date(year=2023, month=7, day=17)

    def test_update_customer_response_token_for_email_notification_id(
        self,
        mock_export_win_tasks_notify_gateway,
    ):
        """
        Test email notification id being saved into customer response model
        """
        notification_id = uuid.uuid4()
        mock_export_win_tasks_notify_gateway.send_email_notification = mock.Mock(
            return_value={'id': notification_id},
        )
        customer_response = CustomerResponseFactory()
        customer_response_token = CustomerResponseTokenFactory(
            customer_response=customer_response,
        )
        send_export_win_email_notification_via_rq(
            customer_response_token.company_contact.email,
            uuid.uuid4(),
            {},
            update_customer_response_token_for_email_notification_id,
            customer_response_token.id,
            NotifyServiceName.export_win,
        )
        customer_response_token.refresh_from_db()

        assert customer_response_token.email_notification_id == notification_id

    def test_customer_response_token_no_email_notification_id(
        self,
        mock_job_scheduler,
    ):
        """
        Tests the notify_export_win_contact_by_rq_email.

        It should schedule a task to:
            * notify a client
            * trigger a second task to store the notification_id
        """
        contact_email_address = 'foo@example.com'
        template_id = str(uuid.uuid4())
        context = {}
        token_id = uuid.uuid4()

        notify_export_win_contact_by_rq_email(
            contact_email_address,
            template_id,
            context,
            update_customer_response_token_for_email_notification_id,
            token_id,
        )
        mock_job_scheduler.assert_called_once_with(
            function=send_export_win_email_notification_via_rq,
            function_args=(
                contact_email_address,
                template_id,
                context,
                update_customer_response_token_for_email_notification_id,
                token_id,
                NotifyServiceName.export_win,
            ),
            retry_backoff=True,
            max_retries=5,
        )

        mock_job_scheduler.reset_mock()
        notify_export_win_contact_by_rq_email(
            contact_email_address,
            template_id,
            context,
            update_customer_response_token_for_email_notification_id,
            token_id,
        )
        mock_job_scheduler.assert_called_once_with(
            function=send_export_win_email_notification_via_rq,
            function_args=(
                contact_email_address,
                template_id,
                context,
                update_customer_response_token_for_email_notification_id,
                token_id,
                NotifyServiceName.export_win,
            ),
            retry_backoff=True,
            max_retries=5,
        )

    def test_update_notify_email_delivery_status_for_customer_response_token(
        self,
        mock_export_win_tasks_notify_gateway,
    ):
        """
        Test email delivery status being updated into customer response token model
        """
        customer_response = CustomerResponseFactory()
        mock_export_win_tasks_notify_gateway.get_notification_by_id = mock.Mock(
            return_value={'status': 'delivered'},
        )
        email_notification_id = uuid.uuid4()
        with freeze_time(self.current_date - relativedelta(days=6)):
            customer_response_token_too_old = CustomerResponseTokenFactory(
                customer_response=customer_response,
                email_delivery_status=EmailDeliveryStatus.UNKNOWN,
                email_notification_id=uuid.uuid4(),
            )
        with freeze_time(self.current_date - relativedelta(days=3)):
            customer_response_token_to_update = CustomerResponseTokenFactory(
                customer_response=customer_response,
                email_delivery_status=EmailDeliveryStatus.UNKNOWN,
                email_notification_id=email_notification_id,
            )

        status_updated_on = self.current_date - relativedelta(days=1)

        with freeze_time(status_updated_on):
            update_notify_email_delivery_status_for_customer_response_token()
        with freeze_time(self.current_date):
            update_notify_email_delivery_status_for_customer_response_token()
        customer_response_token_too_old.refresh_from_db()
        customer_response_token_to_update.refresh_from_db()

        assert (
            customer_response_token_too_old.email_delivery_status
            == EmailDeliveryStatus.UNKNOWN
        )
        assert (
            customer_response_token_to_update.email_delivery_status
            == EmailDeliveryStatus.DELIVERED
        )

        mock_export_win_tasks_notify_gateway.get_notification_by_id.assert_called_once_with(
            email_notification_id,
            notify_service_name=NotifyServiceName.export_win,
        )


def test_get_all_fields_for_client_email_receipt_success():
    customer_response = CustomerResponseFactory()
    token = CustomerResponseTokenFactory(customer_response=customer_response)
    result = get_all_fields_for_client_email_receipt(
        token,
        customer_response,
    )
    """
    Testing to get all fields for client email receipt
    """
    # Assertions for the expected values
    win = customer_response.win
    assert result['customer_email'] == token.company_contact.email
    assert result['country_destination'] == win.country.name
    assert result['client_firstname'] == token.company_contact.first_name
    assert result['lead_officer_name'] == win.lead_officer.name
    assert result['goods_services'] == win.goods_vs_services.name
    # Compare the generated URL with the expected URL using the specific ID
    assert result['url'] == f'{settings.EXPORT_WIN_CLIENT_REVIEW_WIN_URL}/{str(token.id)}'


@pytest.mark.django_db
@freeze_time('2023-12-11')
def test_create_token_for_contact_without_existing_unexpired_token():
    """
    Testing the create token where no existing unexpired token
    """
    mock_customer_response = CustomerResponseFactory()
    mock_contact = ContactFactory()
    new_token = create_token_for_contact(mock_contact, mock_customer_response)
    assert new_token.id is not None
    token_exists = CustomerResponseToken.objects.filter(
        id=new_token.id,
        company_contact=mock_contact,
        customer_response=mock_customer_response,
    ).exists()
    assert token_exists is True
    expected_time = datetime.utcnow() + timedelta(days=7)
    assert expected_time == new_token.expires_on


@pytest.mark.django_db
@freeze_time('2023-12-11')
def test_create_token_with_existing_unexpired_token():
    """
    Testing the creation token where there is existing unexpired token
    """
    mock_customer_response = CustomerResponseFactory()
    mock_contact = ContactFactory()
    with freeze_time('2023-12-10'):
        existing_token = CustomerResponseTokenFactory(
            company_contact=mock_contact,
            customer_response=mock_customer_response,
            expires_on=datetime.utcnow() + timedelta(days=1),
        )
    new_token = create_token_for_contact(mock_contact, mock_customer_response)
    assert new_token.id is not None
    assert new_token.id != existing_token.id
    expected_time = datetime.utcnow() + timedelta(days=7)
    assert expected_time == new_token.expires_on
    existing_token.refresh_from_db()
    utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
    assert existing_token.expires_on <= utc_now


@pytest.mark.django_db
@freeze_time('2023-12-11')
def test_create_token_with_existing_expired_and_unexpired_tokens():
    """
    Testing the creation of a token where there are existing multiple tokens,
    both in expired and unexpired states
    """
    mock_customer_response = CustomerResponseFactory()
    mock_contact = ContactFactory()
    with freeze_time('2023-12-09'):
        expired_token = CustomerResponseTokenFactory(
            company_contact=mock_contact,
            customer_response=mock_customer_response,
            expires_on=datetime.utcnow() - timedelta(days=1),
        )
    with freeze_time('2023-12-10'):
        existing_token = CustomerResponseTokenFactory(
            company_contact=mock_contact,
            customer_response=mock_customer_response,
            expires_on=datetime.utcnow() + timedelta(days=1),
        )
    new_token = create_token_for_contact(mock_contact, mock_customer_response)
    assert new_token.id is not None
    assert new_token.id != existing_token.id
    expected_time = datetime.utcnow() + timedelta(days=7)
    assert expected_time == new_token.expires_on
    expired_token.refresh_from_db()
    utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
    assert expired_token.expires_on <= utc_now
    existing_token.refresh_from_db()
    assert existing_token.expires_on <= utc_now


def test_get_all_fields_for_lead_officer_email_receipt_no_success():
    customer_response = CustomerResponseFactory()
    token = CustomerResponseTokenFactory(customer_response=customer_response)
    company_contact = token.company_contact
    win = customer_response.win

    result = get_all_fields_for_lead_officer_email_receipt_no(
        token,
        customer_response,
    )
    """
    Testing to get all fields for lead officer rejected email receipt
    """
    # Assertions for the expected values
    assert result['lead_officer_email'] == win.lead_officer.email
    assert result['country_destination'] == win.country.name
    assert result['client_fullname'] == company_contact.name
    assert result['lead_officer_first_name'] == win.lead_officer.first_name
    assert result['goods_services'] == win.goods_vs_services.name
    assert result['client_company_name'] == company_contact.company.name
    assert result['url'] == settings.EXPORT_WIN_LEAD_OFFICER_REVIEW_WIN_URL.format(
        uuid=win.id)


def test_get_all_fields_for_lead_officer_email_receipt_yes_success():
    customer_response = CustomerResponseFactory()
    token = CustomerResponseTokenFactory(customer_response=customer_response)
    company_contact = token.company_contact
    win = customer_response.win

    # Create breakdown values of win in batch
    BreakdownFactory.create_batch(5, win=win, value=10000)

    result = get_all_fields_for_lead_officer_email_receipt_yes(
        token,
        customer_response,
    )

    breakdowns = Breakdown.objects.filter(win=win)
    expected_total_export_win_value = breakdowns.aggregate(total_value=Sum('value'))[
        'total_value']

    """
    Testing to get all fields for lead officer approved email receipt (with total_export_win_value)
    """
    # Assertions for the expected values
    assert result['lead_officer_email'] == win.lead_officer.email
    assert result['country_destination'] == win.country.name
    assert result['client_fullname'] == company_contact.name
    assert result['lead_officer_first_name'] == win.lead_officer.first_name
    assert result['total_export_win_value'] == expected_total_export_win_value
    assert result['goods_services'] == win.goods_vs_services.name
    assert result['client_company_name'] == company_contact.company.name
    assert result['url'] == settings.EXPORT_WIN_LEAD_OFFICER_REVIEW_WIN_URL.format(
        uuid=win.id)
