#!/usr/bin/env python3
"""Merge multiple Daily Signal Editor item JSON files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from score_items import item_list, load_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("inputs", nargs="+")
    args = parser.parse_args()

    items: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in args.inputs:
        payload = load_json(path)
        for item in item_list(payload):
            key = str(item.get("id") or item.get("url") or item.get("title"))
            if key in seen:
                continue
            seen.add(key)
            items.append(item)
        if isinstance(payload, dict) and payload.get("errors"):
            errors.extend(payload["errors"])

    Path(args.output).write_text(
        json.dumps({"items": items, "errors": errors}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {len(items)} merged items to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
