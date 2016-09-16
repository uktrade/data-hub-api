from core.utils import format_es_results


def test_format_es_results():
    hits = [
        {
            '_type': 'foo',
            '_id': 1,
            '_source': {'foo': 'bar'}
        },
        {
            '_type': 'bar',
            '_id': 2,
            '_source': {'test': 'pizza'}
        }
    ]
    expected_results = [
        {
            'type': 'foo',
            'id': 1,
            'foo': 'bar'
        },
        {
            'type': 'bar',
            'id': 2,
            'test': 'pizza'
        }
    ]
    assert format_es_results(hits) == expected_results
