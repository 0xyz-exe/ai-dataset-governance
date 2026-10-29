import hashlib
import os
import shutil
from pathlib import Path
from typing import Tuple, Generator, BinaryIO
from backend.app.config import BLOBS_DIR, TEMP_DIR

class ContentAddressedStorage:
    def __init__(self, base_dir: Path = BLOBS_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_blob_path(self, sha256_hash: str) -> Path:
        prefix = sha256_hash[:2]
        dir_path = self.base_dir / prefix
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path / sha256_hash

    def store_bytes(self, data: bytes) -> Tuple[str, int]:
        hasher = hashlib.sha256()
        hasher.update(data)
        digest = hasher.hexdigest()
        size = len(data)

        target = self._get_blob_path(digest)
        if not target.exists():
            target.write_bytes(data)
        return digest, size

    def store_stream(self, stream: BinaryIO) -> Tuple[str, int]:
        hasher = hashlib.sha256()
        temp_file = TEMP_DIR / f"upload_{os.urandom(8).hex()}"
        size = 0

        with open(temp_file, "wb") as f:
            while chunk := stream.read(1024 * 1024):
                hasher.update(chunk)
                f.write(chunk)
                size += len(chunk)

        digest = hasher.hexdigest()
        target = self._get_blob_path(digest)
        if target.exists():
            temp_file.unlink(missing_ok=True)
        else:
            shutil.move(str(temp_file), str(target))

        return digest, size

    def get_blob_path(self, sha256_hash: str) -> Path:
        target = self._get_blob_path(sha256_hash)
        if not target.exists():
            raise FileNotFoundError(f"Blob with hash {sha256_hash} not found in storage")
        return target

    def read_bytes(self, sha256_hash: str) -> bytes:
        path = self.get_blob_path(sha256_hash)
        return path.read_bytes()

    def verify_integrity(self, sha256_hash: str) -> bool:
        try:
            path = self.get_blob_path(sha256_hash)
            hasher = hashlib.sha256()
            with open(path, "rb") as f:
                while chunk := f.read(1024 * 1024):
                    hasher.update(chunk)
            return hasher.hexdigest() == sha256_hash
        except FileNotFoundError:
            return False

storage = ContentAddressedStorage()
