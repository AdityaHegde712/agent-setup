#!/usr/bin/env python3
"""
ml-data-import: quick inspection script
Usage: python scripts/inspect.py <filepath>

Detects format from extension and prints a concise profile:
- File size
- Row/record count
- Column names and dtypes
- Null counts
- First 3 rows (preview)
"""

import sys
import os
import json
from pathlib import Path


def human_size(n_bytes):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n_bytes < 1024:
            return f"{n_bytes:.1f} {unit}"
        n_bytes /= 1024
    return f"{n_bytes:.1f} PB"


def inspect_csv(path):
    import pandas as pd
    df = pd.read_csv(path, sep=None, engine="python", on_bad_lines="warn", nrows=100_000)
    print(f"Format   : CSV/TSV")
    print(f"Shape    : {df.shape[0]:,} rows × {df.shape[1]} cols (first 100k rows)")
    print(f"Columns  :\n{df.dtypes.to_string()}")
    print(f"\nNulls    :\n{df.isnull().sum().to_string()}")
    print(f"\nPreview  :\n{df.head(3).to_string()}")


def inspect_parquet(path):
    import pyarrow.parquet as pq
    import pandas as pd
    meta = pq.read_metadata(path)
    schema = pq.read_schema(path)
    print(f"Format   : Parquet")
    print(f"Rows     : {meta.num_rows:,}")
    print(f"Row grps : {meta.num_row_groups}")
    print(f"Schema   :\n{schema.to_string()}")
    df = pd.read_parquet(path).head(3)
    print(f"\nPreview  :\n{df.to_string()}")


def inspect_json(path):
    import pandas as pd
    # Try JSONL first
    try:
        df = pd.read_json(path, lines=True)
        fmt = "JSONL"
    except Exception:
        df = pd.read_json(path)
        fmt = "JSON"
    print(f"Format   : {fmt}")
    print(f"Shape    : {df.shape[0]:,} rows × {df.shape[1]} cols")
    print(f"Columns  :\n{df.dtypes.to_string()}")
    print(f"\nPreview  :\n{df.head(3).to_string()}")


def inspect_txt(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    non_empty = [l for l in lines if l.strip()]
    total_chars = sum(len(l) for l in lines)
    print(f"Format   : Plain text")
    print(f"Lines    : {len(lines):,} total, {len(non_empty):,} non-empty")
    print(f"Chars    : {total_chars:,}")
    print(f"\nFirst 3 lines:")
    for l in non_empty[:3]:
        print(f"  {l.rstrip()}")


def inspect_sqlite(path):
    import sqlite3
    import pandas as pd
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cur.fetchall()]
    print(f"Format   : SQLite")
    print(f"Tables   : {tables}")
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM '{t}';")
        count = cur.fetchone()[0]
        cur.execute(f"PRAGMA table_info('{t}');")
        cols = [(r[1], r[2]) for r in cur.fetchall()]
        print(f"\n  [{t}]  {count:,} rows")
        for name, dtype in cols:
            print(f"    {name} ({dtype})")
        df = pd.read_sql_query(f"SELECT * FROM '{t}' LIMIT 3;", conn)
        print(f"\n  Preview:\n{df.to_string()}")
    conn.close()


def inspect_log(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    non_empty = [l.rstrip() for l in lines if l.strip()]

    # Try to detect JSON log lines
    json_count = 0
    for line in non_empty[:50]:
        try:
            json.loads(line)
            json_count += 1
        except Exception:
            pass

    print(f"Format   : Log file")
    print(f"Lines    : {len(non_empty):,} non-empty")
    if json_count > len(non_empty[:50]) * 0.7:
        print(f"Structure: JSON log lines (detected)")
    else:
        print(f"Structure: Semi-structured / unstructured text")
    print(f"\nFirst 5 lines:")
    for l in non_empty[:5]:
        print(f"  {l}")


HANDLERS = {
    ".csv": inspect_csv,
    ".tsv": inspect_csv,
    ".parquet": inspect_parquet,
    ".parq": inspect_parquet,
    ".json": inspect_json,
    ".jsonl": inspect_json,
    ".ndjson": inspect_json,
    ".txt": inspect_txt,
    ".text": inspect_txt,
    ".corpus": inspect_txt,
    ".sqlite": inspect_sqlite,
    ".db": inspect_sqlite,
    ".sqlite3": inspect_sqlite,
    ".log": inspect_log,
    ".out": inspect_log,
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/inspect.py <filepath>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Error: {path} not found")
        sys.exit(1)

    ext = path.suffix.lower()
    handler = HANDLERS.get(ext)

    print(f"File     : {path}")
    print(f"Size     : {human_size(path.stat().st_size)}")
    print()

    if handler is None:
        print(f"Unknown extension '{ext}'. Trying as plain text.")
        inspect_txt(path)
    else:
        try:
            handler(path)
        except ImportError as e:
            missing = str(e).split("'")[1] if "'" in str(e) else str(e)
            print(f"Missing library: {missing}")
            print(f"Install with: pip install {missing}")
            sys.exit(1)


if __name__ == "__main__":
    main()
