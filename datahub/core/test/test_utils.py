from datahub.core.utils import slice_iterable_into_chunks


def test_slice_iterable_into_chunks():
    """Test slice iterable into chunks."""
    size = 10
    iterable = range(100)
    chunks = list(slice_iterable_into_chunks(iterable, size, lambda x: x))
    assert len(chunks) == 10
