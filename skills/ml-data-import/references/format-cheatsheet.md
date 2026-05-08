# Format Cheatsheet

Quick one-page reference for all six formats.

| Format  | Extension(s)              | Library              | Preserves types? | Streaming? | Human-readable? |
| ------- | ------------------------- | -------------------- | ---------------- | ---------- | --------------- |
| CSV     | `.csv`, `.tsv`            | `pandas`             | ✗ (inferred)    | ✓ (chunks) | ✓               |
| Parquet | `.parquet`, `.parq`       | `pyarrow`, `pandas`  | ✓               | ✓ (pyarrow dataset) | ✗         |
| JSON    | `.json`                   | `json`, `pandas`     | ✓               | Via `ijson` | ✓              |
| JSONL   | `.jsonl`, `.ndjson`       | `json`, `pandas`     | ✓               | ✓ (line-by-line) | ✓         |
| TXT     | `.txt`, `.corpus`         | stdlib               | N/A             | ✓ (line-by-line) | ✓         |
| SQLite  | `.sqlite`, `.db`          | `sqlite3` (stdlib)   | ✓               | Via SQL LIMIT/OFFSET | ✗   |
| Log     | `.log`, `.out`            | stdlib + `re`/`json` | Parsed          | ✓           | ✓               |

---

## One-liner load commands

```python
# CSV
df = pd.read_csv("f.csv")

# TSV
df = pd.read_csv("f.tsv", sep="\t")

# Parquet
df = pd.read_parquet("f.parquet")

# JSON (array of records)
df = pd.read_json("f.json", orient="records")

# JSONL
df = pd.read_json("f.jsonl", lines=True)

# SQLite
import sqlite3; conn = sqlite3.connect("f.db")
df = pd.read_sql_query("SELECT * FROM table_name;", conn)

# TXT (line-per-sample)
with open("f.txt") as f:
    lines = [l.strip() for l in f if l.strip()]
```

---

## Memory cost rough estimates (1M rows, 10 columns)

| Format      | In-memory size (float64) | Notes                           |
| ----------- | ------------------------ | ------------------------------- |
| CSV         | ~800 MB                  | All strings during parse        |
| Parquet     | ~80–160 MB               | Compressed + columnar           |
| JSONL       | ~600–1200 MB             | Depends on nesting              |
| SQLite      | Varies                   | Only rows fetched are loaded    |

---

## When to use Polars instead of pandas

Switch to Polars when:

- File > 500 MB
- You need lazy evaluation (query planning without loading)
- You want multi-threaded parsing out of the box

```python
import polars as pl

df = pl.read_csv("big.csv")
df = pl.read_parquet("big.parquet")
df = pl.read_ndjson("big.jsonl")
```

Polars DataFrames have a `.to_pandas()` method if downstream libraries
require pandas.
