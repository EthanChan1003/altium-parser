"""Custom exception hierarchy for Altium parser."""


class AltiumParserError(Exception):
    """Base exception for all Altium parser errors."""


class OleOpenError(AltiumParserError):
    """Failed to open file as OLE compound document."""


class OleStreamNotFoundError(AltiumParserError):
    """Required OLE stream or storage not found."""

    def __init__(self, stream_name: str, file_path: str = ""):
        self.stream_name = stream_name
        self.file_path = file_path
        msg = f"OLE stream '{stream_name}' not found"
        if file_path:
            msg += f" in '{file_path}'"
        super().__init__(msg)


class UnknownRecordTypeError(AltiumParserError):
    """Encountered an unknown record type during parsing."""

    def __init__(self, record_type: int, offset: int = -1):
        self.record_type = record_type
        self.offset = offset
        msg = f"Unknown record type {record_type}"
        if offset >= 0:
            msg += f" at byte offset {offset}"
        super().__init__(msg)


class CorruptedDataError(AltiumParserError):
    """Data is corrupted or truncated."""

    def __init__(self, message: str = "Data is corrupted or truncated", offset: int = -1):
        self.offset = offset
        if offset >= 0:
            message += f" (at byte offset {offset})"
        super().__init__(message)


class UnsupportedFileVersionError(AltiumParserError):
    """File version is not supported by this parser."""

    def __init__(self, version: str, file_path: str = ""):
        self.version = version
        self.file_path = file_path
        msg = f"Unsupported file version '{version}'"
        if file_path:
            msg += f" in '{file_path}'"
        super().__init__(msg)
