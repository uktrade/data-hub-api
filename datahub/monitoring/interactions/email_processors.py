from prometheus_client import Counter

from datahub.monitoring import registry
from datahub.monitoring.utils import push_to_gateway


JOB_NAME = 'calendar-invite-ingest'

failure_counter = Counter(
    'email_ingest_failure',
    'Number of failed calendar invite ingestions',
    ('domain', ),
    registry=registry,
)

success_counter = Counter(
    'email_ingest_success',
    'Number of successful calendar invite ingestions',
    ('domain', ),
    registry=registry,
)


def get_adviser_domain(adviser):
    """
    Return domain for the adviser's email.
    """
    return adviser.get_current_email().split('@')[-1]


def record_failure(adviser):
    """
    Increment the failure counter.
    """
    failure_counter.labels(domain=get_adviser_domain(adviser)).inc()
    push_to_gateway(JOB_NAME)


def record_success(adviser):
    """
    Increment the success counter.
    """
    success_counter.labels(domain=get_adviser_domain(adviser)).inc()
    push_to_gateway(JOB_NAME)
