import pytest

pytestmark = pytest.mark.django_db


def test_schedule_sync_investment_projects_of_subsidiary_companies(opensearch_with_signals):
    pass
    # """Tests if company gets synced to OpenSearch."""
    # test_name = 'very_hard_to_find_company'
    # CompanyFactory(
    #     name=test_name,
    # )
    # opensearch_with_signals.indices.refresh()

    # result = get_basic_search_query(Company, test_name).execute()

    # assert result.hits.total.value == 1


def test_sync_investment_projects_of_subsidiary_companies(opensearch_with_signals):
    pass
    # """Tests if company gets updated in OpenSearch."""
    # test_name = 'very_hard_to_find_company_international'
    # company = CompanyFactory(
    #     name=test_name,
    # )
    # new_test_name = 'very_hard_to_find_company_local'
    # company.name = new_test_name
    # company.save()
    # opensearch_with_signals.indices.refresh()

    # result = get_basic_search_query(Company, new_test_name).execute()

    # assert result.hits.total.value == 1
    # assert result.hits[0].id == str(company.id)
