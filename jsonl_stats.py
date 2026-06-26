#!/usr/bin/env python3
"""jsonl-stats: report simple statistics over JSON Lines files."""

import argparse
import json
import sys
from collections import Counter
from typing import Any, Dict, Iterable, TextIO


TYPE_NAMES = {
    type(None): "null",
    bool: "bool",
    int: "int",
    float: "float",
    str: "str",
    list: "list",
    dict: "dict",
}


def type_name(value: Any) -> str:
    """Return a human-readable type label for *value*."""
    return TYPE_NAMES.get(type(value), type(value).__name__)


def analyze_records(records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute key frequency and per-key type histograms.

    Returns a dict with:
      - record_count: number of records processed
      - key_frequency: {key: number of records containing key}
      - type_histograms: {key: {type: count}}
    """
    key_frequency: Counter = Counter()
    type_histograms: Dict[str, Counter] = {}
    record_count = 0

    for record in records:
        record_count += 1
        for key, value in record.items():
            key_frequency[key] += 1
            # Use get() to avoid creating unnecessary Counter objects
            hist = type_histograms.get(key)
            if hist is None:
                hist = Counter()
                type_histograms[key] = hist
            hist[type_name(value)] += 1

    return {
        "record_count": record_count,
        "key_frequency": dict(key_frequency.most_common()),
        "type_histograms": {
            key: dict(hist.most_common())
            for key, hist in type_histograms.items()
        },
    }


def parse_jsonl(stream: TextIO) -> Iterable[Dict[str, Any]]:
    """Yield top-level JSON objects from a JSON Lines stream."""
    for line_no, line in enumerate(stream, start=1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            # Create a new exception with better context while preserving the original
            raise json.JSONDecodeError(
                f"invalid JSON on line {line_no}: {exc.msg}",
                line,
                exc.pos,
            ) from exc
        if not isinstance(obj, dict):
            raise ValueError(f"line {line_no}: expected a JSON object, got {type_name(obj)}")
        yield obj


def format_text(stats: Dict[str, Any]) -> str:
    """Render stats as a concise plain-text report."""
    lines = [
        f"record_count: {stats['record_count']}",
        "",
        "key_frequency:",
    ]
    if stats["key_frequency"]:
        max_key = max(len(k) for k in stats["key_frequency"])
        for key, count in stats["key_frequency"].items():
            lines.append(f"  {key:<{max_key}} {count}")
    else:
        lines.append("  (none)")

    lines.append("")
    lines.append("type_histograms:")
    if stats["type_histograms"]:
        for key, hist in stats["type_histograms"].items():
            parts = ", ".join(f"{t}: {c}" for t, c in hist.items())
            lines.append(f"  {key}: {parts}")
    else:
        lines.append("  (none)")

    return "\n".join(lines) + "\n"


def main(argv: Iterable[str] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="jsonl-stats",
        description="Report record count, key frequency, and per-key type histograms for a JSONL file.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="JSONL file to analyze (default: stdin)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="output the report as JSON",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="-",
        help="write report to FILE instead of stdout",
    )
    args = parser.parse_args(argv)

    in_stream: TextIO
    if args.file == "-":
        in_stream = sys.stdin
    else:
        try:
            in_stream = open(args.file, "r", encoding="utf-8")
        except OSError as exc:
            print(f"error: cannot open {args.file!r}: {exc}", file=sys.stderr)
            return 1

    try:
        stats = analyze_records(parse_jsonl(in_stream))
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        if in_stream is not sys.stdin:
            in_stream.close()

    out_stream: TextIO
    if args.output == "-":
        out_stream = sys.stdout
    else:
        try:
            out_stream = open(args.output, "w", encoding="utf-8")
        except OSError as exc:
            print(f"error: cannot open {args.output!r}: {exc}", file=sys.stderr)
            return 1

    try:
        if args.json:
            json.dump(stats, out_stream, indent=2)
            out_stream.write("\n")
        else:
            out_stream.write(format_text(stats))
    finally:
        if out_stream is not sys.stdout:
            out_stream.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
