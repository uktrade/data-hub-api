from api.models.chcompany import CHCompany
from api.models.searchitem import SearchItem
from datahubapi import settings


RESULT_SIZE = 10


def delete_for_company_number(company_number):
    # Find the existing entry to get it's id
    find_query = {
        "query": {
            "constant_score": {
                "filter": {
                    "term": {
                        "company_number": company_number
                    }
                }
            }
        }
    }

    es_results = settings.ES_CLIENT.search(index=SearchItem.Meta.es_index_name,
                                           doc_type=SearchItem.Meta.es_type_name,
                                           body=find_query)

    if es_results['hits']['total'] == 1:
        index_id = es_results['hits']['hits'][0]['_id']
        delete_for_id(index_id)


def delete_for_source_id(source_id):
    # Find the existing entry to get it's id
    find_query = {
        "query": {
            "constant_score": {
                "filter": {
                    "term": {
                        "source_id": source_id
                    }
                }
            }
        }
    }

    es_results = settings.ES_CLIENT.search(index=SearchItem.Meta.es_index_name,
                                           doc_type=SearchItem.Meta.es_type_name,
                                           body=find_query)

    if es_results['hits']['total'] == 1:
        index_id = es_results['hits']['hits'][0]['_id']
        delete_for_id(index_id)


def delete_for_id(index_id):
    settings.ES_CLIENT.delete(index=SearchItem.Meta.es_index_name,
                              doc_type=SearchItem.Meta.es_type_name,
                              id=index_id,
                              refresh=True)


def search(term, filters=None, page=1):

    if filters is None:
        filters = {}
    from_ = (page - 1) * RESULT_SIZE

    query = {
        "size": RESULT_SIZE,
        "from": from_,
        "query": {
            "query_string": {"query": term},
        },
        "aggregations": {
            "result_type": {
                "terms": {
                    "field": "result_type"
                }
            }
        }
    }

    if len(filters) > 0:
        query_filters = []
        for key, value in filters.items():
            query_filters.append({"term": {key: value}})

        query["filter"] = {
            "bool": {
                "must": query_filters
            }
        }

    index_name = SearchItem.Meta.es_index_name
    es_results = settings.ES_CLIENT.search(index=index_name, body=query, )
    result = transform_search_result(es_result=es_results)
    return result


# Transform an elastic search result into a format that is easier to use
# and includes the original parameters
def transform_search_result(es_result):
    result = {
        "total": es_result["hits"]["total"],
        "max_score": es_result["hits"]["max_score"],
        "hits": es_result["hits"]["hits"],
    }

    facets = {}
    aggregations = es_result["aggregations"]

    for aggregation_key, aggregation_value in aggregations.items():
        facets[aggregation_key] = []
        for aggregation_bucket in aggregation_value["buckets"]:
            facets[aggregation_key]\
                .append({"value": aggregation_bucket["key"], "total": aggregation_bucket["doc_count"]})

    result["facets"] = facets
    return result


# Generate an elastic search item from a company record
def search_item_from_company(company):
    ch = CHCompany.objects.get(pk=company.company_number)
    if company.company_number and len(company.company_number) > 0:
        result_source = 'COMBINED'
    else:
        result_source = 'DIT'

    return SearchItem(
        source_id=company.id,
        result_source=result_source,
        result_type='COMPANY',
        title=ch.company_name,
        address_1=ch.registered_address_address_1,
        address_2=ch.registered_address_address_2,
        address_town=ch.registered_address_town,
        address_county=ch.registered_address_county,
        address_country=ch.registered_address_country,
        address_postcode=ch.registered_address_postcode,
        alt_title=company.trading_name,
        alt_address_1=company.trading_address_1,
        alt_address_2=company.trading_address_2,
        alt_address_town=company.trading_address_town,
        alt_address_county=company.trading_address_county,
        alt_address_country=company.trading_address_country,
        alt_address_postcode=company.trading_address_postcode,
        company_number=company.company_number,
        incorporation_date=ch.incorporation_date
    )


# Generate an elastic search item from a contact record
def search_item_from_contact(contact):
    return SearchItem(
        source_id=contact.id,
        result_source='DIT',
        result_type='CONTACT',
        title=contact.first_name + ' ' + contact.last_name,
        address_1=contact.address_1,
        address_2=contact.address_2,
        address_town=contact.address_town,
        address_county=contact.address_county,
        address_country=contact.address_country,
        address_postcode=contact.address_postcode
    )


# Generate an elastic search item from an interaction record
def search_item_from_interaction(interaction):
    return SearchItem(
        source_id=interaction.id,
        result_source='DIT',
        result_type='INTERACTION',
        title=interaction.title
    )
