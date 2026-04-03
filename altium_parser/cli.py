"""Command-line interface for the Altium Designer file parser."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import __version__
from .registry import parse_file, get_file_type, SUPPORTED_EXTENSIONS
from .serializers.json_serializer import serialize_to_json
from .serializers.xml_serializer import serialize_to_xml


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="altium-parser",
        description="Altium Designer project file parser — extracts components, nets, "
                    "traces, layers and coordinates to structured JSON/XML.",
    )
    parser.add_argument(
        "input_file",
        help=f"Path to Altium file ({', '.join(sorted(SUPPORTED_EXTENSIONS))})",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: <input_basename>.<format>)",
    )
    parser.add_argument(
        "-f", "--format",
        choices=["json", "xml", "both"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="Pretty-print output (default: on)",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Compact output (no indentation)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging verbosity (default: INFO)",
    )
    parser.add_argument(
        "--dump-structure",
        action="store_true",
        help="Dump OLE file structure and exit (for debugging)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"altium-parser {__version__}",
    )

    args = parser.parse_args(argv)

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s: %(message)s",
    )
    logger = logging.getLogger("altium_parser")

    input_path = Path(args.input_file)
    if not input_path.exists():
        logger.error("File not found: %s", input_path)
        return 1

    pretty = not args.compact

    # Dump OLE structure if requested
    if args.dump_structure:
        return _dump_structure(input_path)

    # Parse the file
    try:
        file_type = get_file_type(input_path)
        logger.info("Parsing %s as %s...", input_path.name, file_type)
        model = parse_file(input_path)
    except ValueError as e:
        logger.error(str(e))
        return 1
    except Exception as e:
        logger.error("Failed to parse '%s': %s", input_path.name, e)
        if args.log_level == "DEBUG":
            import traceback
            traceback.print_exc()
        return 1

    # Determine output paths
    stem = input_path.stem
    out_dir = Path(args.output).parent if args.output else input_path.parent

    # Serialize and write output
    formats = ["json", "xml"] if args.format == "both" else [args.format]

    for fmt in formats:
        if args.output and args.format != "both":
            out_path = Path(args.output)
        else:
            out_path = out_dir / f"{stem}.{fmt}"

        try:
            if fmt == "json":
                result = serialize_to_json(model, file_type, input_path.name, out_path, pretty)
            else:
                result = serialize_to_xml(model, file_type, input_path.name, out_path, pretty)

            logger.info("Written %s output to: %s", fmt.upper(), out_path)
        except Exception as e:
            logger.error("Failed to write %s: %s", fmt.upper(), e)
            if args.log_level == "DEBUG":
                import traceback
                traceback.print_exc()
            return 1

    return 0


def _dump_structure(file_path: Path) -> int:
    """Dump the OLE structure of a file."""
    ext = file_path.suffix.lower()
    if ext == ".prjpcb":
        print(f"File: {file_path.name}")
        print("Type: Plain text INI format (not OLE)")
        print("---")
        content = file_path.read_text(encoding="utf-8", errors="replace")
        print(content[:5000])
        return 0

    try:
        from .core.ole_reader import OleReader
        with OleReader(file_path) as ole:
            print(ole.dump_structure())
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
