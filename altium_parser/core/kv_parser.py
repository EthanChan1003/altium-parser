"""Parser for pipe-delimited |KEY=VALUE records used in SchDoc and SchLib files."""

from __future__ import annotations


def parse_kv_record(data: bytes, encoding: str = "latin-1") -> dict[str, str]:
    """Parse a pipe-delimited |KEY=VALUE byte string into a dict.

    Altium schematic records use the format:
        |KEY1=VALUE1|KEY2=VALUE2|KEY3=VALUE3

    Leading and trailing pipes are handled. Values may contain '=' characters.
    Empty values are preserved as empty strings.
    """
    text = data.decode(encoding, errors="replace")
    text = text.rstrip("\x00").strip()

    result: dict[str, str] = {}
    if not text:
        return result

    # Split on | and filter empty segments
    parts = text.split("|")
    for part in parts:
        part = part.strip()
        if not part:
            continue
        eq_pos = part.find("=")
        if eq_pos < 0:
            # Key with no value
            result[part.upper()] = ""
        else:
            key = part[:eq_pos].strip().upper()
            value = part[eq_pos + 1:]
            result[key] = value

    return result


def parse_pcb_kv_record(data: bytes, encoding: str = "latin-1") -> dict[str, str]:
    """Parse PcbDoc key-value records.

    PcbDoc uses the same pipe-delimited format but the data stream
    may have a leading record type identifier. This function handles
    both cases.
    """
    # Some PcbDoc streams have a 0x00 terminated string prefix before the KV data
    # Try to find the first pipe character
    text = data.decode(encoding, errors="replace")
    text = text.rstrip("\x00").strip()

    # If the text doesn't start with |, try to find the first |
    pipe_pos = text.find("|")
    if pipe_pos > 0:
        text = text[pipe_pos:]

    return parse_kv_record(text.encode(encoding), encoding)
