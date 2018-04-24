from datahub.search.bulk_sync import _batch_rows


def test_batch_rows():
    """Tests _batch_rows."""
    rows = ({}, {}, {})

    res = list(_batch_rows(rows, batch_size=2))

    assert len(res) == 2
    assert len(res[0]) == 2
    assert len(res[1]) == 1
