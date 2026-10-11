import os
from pathlib import Path
from app.core.config import STORAGE_ROOT
from uuid import uuid4

class LocalFileStorage:

    def __init__(self,storage_root:Path):
        self.storage_root=storage_root

    def get_full_path(self,storage_key:str):
        root = self.storage_root.resolve()
        path = (root / storage_key).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Storage key escapes the storage root")
        return path

    def generate_storage_key(self,original_filename:str|None)->str:

        extension=Path(original_filename or "").suffix.lower()

        unique_filename=(f"{uuid4()}{extension}")

        return (f"documents/{unique_filename}")

    def save(self,contents:bytes,original_filename:str|None)->str:

        storage_key=self.generate_storage_key(original_filename)

        full_path=self.get_full_path(storage_key)

        full_path.parent.mkdir(parents=True,exist_ok=True)

        full_path.write_bytes(contents)
        return storage_key

    def delete(self,storage_key:str)->None:
        full_path=self.get_full_path(storage_key)

        full_path.unlink(missing_ok=True)



file_storage=LocalFileStorage(storage_root=STORAGE_ROOT)
