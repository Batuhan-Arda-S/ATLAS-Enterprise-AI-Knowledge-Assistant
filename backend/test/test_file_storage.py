from app.services.file_storage import LocalFileStorage
import pytest

def test_file_storage_saves_file(tmp_path):
    storage=LocalFileStorage(storage_root=tmp_path)

    contents = b"Enterprise AI document"

    storage_key=storage.save(contents=contents,original_filename="policy.pdf")

    full_path=storage.get_full_path(storage_key)

    assert full_path.exists()
    assert full_path.read_bytes() == contents

def test_storage_keys_are_unique(tmp_path):
    storage=LocalFileStorage(storage_root=tmp_path)

    first_key=storage.generate_storage_key("policy.pdf")
    second_key=storage.generate_storage_key("policy.pdf")

    assert first_key != second_key
    assert first_key.endswith(".pdf")
    assert second_key.endswith(".pdf")

def test_file_storage_deletes_file(tmp_path):
    storage=LocalFileStorage(storage_root=tmp_path)

    storage_key=storage.save(contents=b"temporary file",original_filename="temporary.txt")

    full_path=storage.get_full_path(storage_key)

    assert full_path.exists()

    storage.delete(storage_key)

    assert not full_path.exists()


def test_storage_rejects_traversal_key(tmp_path):
    storage = LocalFileStorage(storage_root=tmp_path)
    with pytest.raises(ValueError):
        storage.get_full_path("../outside.txt")
    with pytest.raises(ValueError):
        storage.get_full_path(str(tmp_path.parent / "outside.txt"))
