"""OLE Compound Document reader abstraction over olefile."""

from __future__ import annotations

import logging
from pathlib import Path

import olefile

from .exceptions import OleOpenError, OleStreamNotFoundError

logger = logging.getLogger(__name__)


class OleReader:
    """Context-manager wrapper around olefile for reading Altium OLE files."""

    def __init__(self, file_path: str | Path):
        self._file_path = Path(file_path)
        self._ole: olefile.OleFileIO | None = None

    def __enter__(self) -> OleReader:
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def open(self) -> None:
        if not self._file_path.exists():
            raise FileNotFoundError(f"File not found: {self._file_path}")
        try:
            self._ole = olefile.OleFileIO(str(self._file_path))
        except Exception as e:
            raise OleOpenError(
                f"Cannot open '{self._file_path}' as OLE compound document: {e}"
            ) from e

    def close(self) -> None:
        if self._ole:
            self._ole.close()
            self._ole = None

    @property
    def file_path(self) -> Path:
        return self._file_path

    def list_streams(self) -> list[str]:
        """List all stream paths in the OLE file."""
        if not self._ole:
            raise OleOpenError("OLE file is not open")
        return ["/".join(entry) for entry in self._ole.listdir(streams=True, storages=False)]

    def list_storages(self) -> list[str]:
        """List all storage paths in the OLE file."""
        if not self._ole:
            raise OleOpenError("OLE file is not open")
        return ["/".join(entry) for entry in self._ole.listdir(streams=False, storages=True)]

    def list_all(self) -> list[str]:
        """List all entries (both streams and storages)."""
        if not self._ole:
            raise OleOpenError("OLE file is not open")
        return ["/".join(entry) for entry in self._ole.listdir(streams=True, storages=True)]

    def has_stream(self, path: str) -> bool:
        """Check if a stream exists at the given path."""
        if not self._ole:
            return False
        # Convert slash-separated to list format for olefile
        parts = path.replace("\\", "/").split("/")
        return self._ole.exists(parts)

    def read_stream(self, path: str) -> bytes:
        """Read the full content of a stream."""
        if not self._ole:
            raise OleOpenError("OLE file is not open")
        parts = path.replace("\\", "/").split("/")
        if not self._ole.exists(parts):
            raise OleStreamNotFoundError(path, str(self._file_path))
        try:
            return self._ole.openstream(parts).read()
        except Exception as e:
            raise OleStreamNotFoundError(path, str(self._file_path)) from e

    def read_stream_safe(self, path: str) -> bytes | None:
        """Read a stream, returning None if it doesn't exist."""
        if not self.has_stream(path):
            return None
        try:
            return self.read_stream(path)
        except OleStreamNotFoundError:
            return None

    def get_root_storage_names(self) -> list[str]:
        """Get the names of all top-level storages."""
        if not self._ole:
            raise OleOpenError("OLE file is not open")
        result = []
        for entry in self._ole.listdir(streams=False, storages=True):
            if len(entry) == 1:
                result.append(entry[0])
        return result

    def get_sub_storages(self, parent: str) -> list[str]:
        """Get names of sub-storages under a parent storage."""
        if not self._ole:
            raise OleOpenError("OLE file is not open")
        parent_parts = parent.replace("\\", "/").split("/")
        parent_depth = len(parent_parts)
        result = []
        for entry in self._ole.listdir(streams=False, storages=True):
            if len(entry) == parent_depth + 1 and entry[:parent_depth] == parent_parts:
                result.append(entry[-1])
        return result

    def dump_structure(self) -> str:
        """Return a human-readable dump of the OLE file structure."""
        if not self._ole:
            raise OleOpenError("OLE file is not open")
        lines = [f"OLE Structure: {self._file_path.name}"]
        for entry in self._ole.listdir(streams=True, storages=True):
            path = "/".join(entry)
            try:
                size = self._ole.get_size(entry)
                lines.append(f"  {path} ({size} bytes)")
            except Exception:
                lines.append(f"  {path} (storage)")
        return "\n".join(lines)
