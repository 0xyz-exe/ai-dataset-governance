import pytest
from backend.app.storage import storage

def test_storage_store_and_verify():
    content = b"sample dataset line 1,2,3\nsample line 2,4,5\n"
    digest, size = storage.store_bytes(content)
    assert size == len(content)
    assert len(digest) == 64

    # Verify integrity
    assert storage.verify_integrity(digest) is True

    # Read back
    read_data = storage.read_bytes(digest)
    assert read_data == content

def test_storage_deduplication():
    content = b"duplicate-content-block-test"
    digest1, size1 = storage.store_bytes(content)
    digest2, size2 = storage.store_bytes(content)
    assert digest1 == digest2
    assert size1 == size2
