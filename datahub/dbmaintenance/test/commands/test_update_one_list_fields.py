from io import BytesIO
from itertools import chain

import factory
import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.core.test_utils import random_obj_for_model, random_obj_for_queryset
from datahub.metadata.models import CompanyClassification

pytestmark = pytest.mark.django_db


def save_prev_fields(company, *fields):
    """
    Save the `fields` to different private attributes so that we can compare original
    values against new ones.
    """
    for field in fields:
        setattr(company, f'_prev_{field}', getattr(company, field))


def assert_did_not_change(company, *fields):
    """
    Assert that the company fields did not change.
    It assumes `save_prev_fields` has been called before the potential change.
    """
    for field in fields:
        assert getattr(company, field) == getattr(company, f'_prev_{field}')


def assert_changed(company, *fields):
    """
    Assert that the company fields changed.
    It assumes `save_prev_fields` has been called before the potential change.
    """
    for field in fields:
        assert getattr(company, field) != getattr(company, f'_prev_{field}')


@pytest.mark.parametrize('reset_unmatched', (False, True))
def test_run(s3_stubber, caplog, reset_unmatched):
    """
    Test that the command updates the specified records (ignoring ones with errors).
    If `reset_unmatched` is False, the existing records not in the CSV are kept untouched,
    otherwise they are set to None.
    """
    caplog.set_level('ERROR')

    new_classification = random_obj_for_model(CompanyClassification)
    one_list_companies = CompanyFactory.create_batch(
        8,
        classification=factory.LazyFunction(
            lambda: random_obj_for_queryset(
                CompanyClassification.objects.exclude(pk=new_classification.pk),
            ),
        ),
        one_list_account_owner=factory.SubFactory(AdviserFactory),
    )
    non_one_list_companies = CompanyFactory.create_batch(
        3,
        classification=None,
        one_list_account_owner=None,
    )

    for company in chain(one_list_companies, non_one_list_companies):
        save_prev_fields(company, 'classification_id', 'one_list_account_owner_id')

    advisers = AdviserFactory.create_batch(4)

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,classification_id,one_list_account_owner_id
00000000-0000-0000-0000-000000000000,test,test
{one_list_companies[0].pk},{one_list_companies[0].classification_id},{one_list_companies[0].one_list_account_owner_id}
{one_list_companies[1].pk},{one_list_companies[1].classification_id},{advisers[0].pk}
{one_list_companies[2].pk},{new_classification.pk},{one_list_companies[2].one_list_account_owner_id}
{one_list_companies[3].pk},null,null
{one_list_companies[4].pk},00000000-0000-0000-0000-000000000000,{advisers[1].pk}
{one_list_companies[5].pk},{new_classification.pk},00000000-0000-0000-0000-000000000000
{non_one_list_companies[0].pk},{new_classification.pk},{advisers[2].pk}
{non_one_list_companies[1].pk},00000000-0000-0000-0000-000000000000,{advisers[3].pk}
{non_one_list_companies[2].pk},{new_classification.pk},00000000-0000-0000-0000-000000000000
"""

    s3_stubber.add_response(
        'get_object',
        {'Body': BytesIO(csv_content.encode(encoding='utf-8'))},
        expected_params={
            'Bucket': bucket,
            'Key': object_key,
        },
    )

    call_command('update_one_list_fields', bucket, object_key, reset_unmatched=reset_unmatched)

    for company in chain(one_list_companies, non_one_list_companies):
        company.refresh_from_db()

    # assert exceptions
    assert len(caplog.records) == 5
    assert 'Company matching query does not exist' in caplog.records[0].exc_text
    assert 'CompanyClassification matching query does not exist' in caplog.records[1].exc_text
    assert 'Advisor matching query does not exist' in caplog.records[2].exc_text
    assert 'CompanyClassification matching query does not exist' in caplog.records[3].exc_text
    assert 'Advisor matching query does not exist' in caplog.records[4].exc_text

    # one_list_companies[0]: nothing changed
    assert_did_not_change(one_list_companies[0], 'classification_id', 'one_list_account_owner_id')

    # one_list_companies[1]: only one_list_account_owner_id changed
    assert_changed(one_list_companies[1], 'one_list_account_owner_id')
    assert_did_not_change(one_list_companies[1], 'classification_id')
    assert one_list_companies[1].one_list_account_owner == advisers[0]

    # one_list_companies[2]: only classification_id changed
    assert_did_not_change(one_list_companies[2], 'one_list_account_owner_id')
    assert_changed(one_list_companies[2], 'classification_id')
    assert one_list_companies[2].classification == new_classification

    # one_list_companies[3]: all changed
    assert_changed(one_list_companies[3], 'classification_id', 'one_list_account_owner_id')
    assert one_list_companies[3].classification_id is None
    assert one_list_companies[3].one_list_account_owner_id is None

    # one_list_companies[4]: nothing changed
    assert_did_not_change(one_list_companies[4], 'classification_id', 'one_list_account_owner_id')

    # one_list_companies[5]: nothing changed
    assert_did_not_change(one_list_companies[5], 'classification_id', 'one_list_account_owner_id')

    # non_one_list_companies[0]: all changed
    assert_changed(non_one_list_companies[0], 'classification_id', 'one_list_account_owner_id')
    assert non_one_list_companies[0].one_list_account_owner == advisers[2]
    assert non_one_list_companies[0].classification == new_classification

    # non_one_list_companies[1]: nothing changed
    assert_did_not_change(
        non_one_list_companies[1], 'classification_id', 'one_list_account_owner_id',
    )

    # non_one_list_companies[2]: nothing changed
    assert_did_not_change(
        non_one_list_companies[2], 'classification_id', 'one_list_account_owner_id',
    )

    # one_list_companies[6] / [7]: if reset_unmatched == False => nothing changed else all changed
    if reset_unmatched:
        assert_changed(one_list_companies[6], 'classification_id', 'one_list_account_owner_id')
        assert_changed(one_list_companies[7], 'classification_id', 'one_list_account_owner_id')
        assert one_list_companies[6].classification is None
        assert one_list_companies[6].one_list_account_owner is None

        assert one_list_companies[7].classification is None
        assert one_list_companies[7].one_list_account_owner is None
    else:
        assert_did_not_change(
            one_list_companies[6], 'classification_id', 'one_list_account_owner_id',
        )
        assert_did_not_change(
            one_list_companies[7], 'classification_id', 'one_list_account_owner_id',
        )


@pytest.mark.parametrize('reset_unmatched', (False, ))
def test_simulate(s3_stubber, caplog, reset_unmatched):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('ERROR')

    new_classification = random_obj_for_model(CompanyClassification)
    one_list_companies = CompanyFactory.create_batch(
        8,
        classification=factory.LazyFunction(
            lambda: random_obj_for_queryset(
                CompanyClassification.objects.exclude(pk=new_classification.pk),
            ),
        ),
        one_list_account_owner=factory.SubFactory(AdviserFactory),
    )
    non_one_list_companies = CompanyFactory.create_batch(
        3,
        classification=None,
        one_list_account_owner=None,
    )

    for company in chain(one_list_companies, non_one_list_companies):
        save_prev_fields(company, 'classification_id', 'one_list_account_owner_id')

    advisers = AdviserFactory.create_batch(4)

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,classification_id,one_list_account_owner_id
00000000-0000-0000-0000-000000000000,test,test
{one_list_companies[0].pk},{one_list_companies[0].classification_id},{one_list_companies[0].one_list_account_owner_id}
{one_list_companies[1].pk},{one_list_companies[1].classification_id},{advisers[0].pk}
{one_list_companies[2].pk},{new_classification.pk},{one_list_companies[2].one_list_account_owner_id}
{one_list_companies[3].pk},null,null
{one_list_companies[4].pk},00000000-0000-0000-0000-000000000000,{advisers[1].pk}
{one_list_companies[5].pk},{new_classification.pk},00000000-0000-0000-0000-000000000000
{non_one_list_companies[0].pk},{new_classification.pk},{advisers[2].pk}
{non_one_list_companies[1].pk},00000000-0000-0000-0000-000000000000,{advisers[3].pk}
{non_one_list_companies[2].pk},{new_classification.pk},00000000-0000-0000-0000-000000000000
"""

    s3_stubber.add_response(
        'get_object',
        {'Body': BytesIO(csv_content.encode(encoding='utf-8'))},
        expected_params={
            'Bucket': bucket,
            'Key': object_key,
        },
    )

    call_command(
        'update_one_list_fields',
        bucket,
        object_key,
        reset_unmatched=reset_unmatched,
        simulate=True,
    )

    for company in chain(one_list_companies, non_one_list_companies):
        company.refresh_from_db()

    # assert exceptions
    assert len(caplog.records) == 5
    assert 'Company matching query does not exist' in caplog.records[0].exc_text
    assert 'CompanyClassification matching query does not exist' in caplog.records[1].exc_text
    assert 'Advisor matching query does not exist' in caplog.records[2].exc_text
    assert 'CompanyClassification matching query does not exist' in caplog.records[3].exc_text
    assert 'Advisor matching query does not exist' in caplog.records[4].exc_text

    # assert that nothing really changed
    for company in chain(one_list_companies, non_one_list_companies):
        assert_did_not_change(company, 'classification_id', 'one_list_account_owner_id')


def test_audit_log(s3_stubber, caplog):
    """Test that reversion revisions are created."""
    classifications = CompanyClassification.objects.order_by('?')[:2]
    company_without_change, company_with_change = CompanyFactory.create_batch(
        2,
        classification=classifications[0],
        one_list_account_owner=AdviserFactory(),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,classification_id,one_list_account_owner_id
{company_without_change.pk},{company_without_change.classification_id},{company_without_change.one_list_account_owner_id}
{company_with_change.pk},{classifications[1].pk},{AdviserFactory().pk}
"""

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(csv_content.encode(encoding='utf-8')),
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key,
        },
    )

    call_command('update_one_list_fields', bucket, object_key)

    assert len(caplog.records) == 0

    versions = Version.objects.get_for_object(company_without_change)
    assert versions.count() == 0

    versions = Version.objects.get_for_object(company_with_change)
    assert versions.count() == 1
    comment = versions[0].revision.get_comment()
    assert comment == 'Classification and One List account owner correction.'
