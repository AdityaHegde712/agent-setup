---
name: ml-data-import
description: >
  Load, inspect, and prepare data files for AI/ML workflows. Handles CSV,
  Parquet, JSON, plain-text (TXT), SQLite databases, and log files. Use this
  skill whenever the user wants to read a dataset, explore its schema,
  understand its contents, or prepare it for model training, fine-tuning,
  evaluation, or feature engineering — even if they only say things like
  "load my data", "read this file", "what's in this dataset", "import my
  training data", "connect to my database", or "parse these logs". Always
  use this skill before any downstream ML step (EDA, preprocessing,
  training) when a raw data file is involved.
compatibility: >
  Requires Python 3.8+. Core libraries: pandas, pyarrow (Parquet), sqlite3
  (stdlib). Optional: polars (large files), datasets (HuggingFace),
  jsonlines (JSONL). Install missing libraries via pip.
metadata:
  domain: ai-ml
  version: "1.0"
---

# ML Data Import

Comprehensive guidance for loading and inspecting the six most common raw
data formats encountered in AI/ML problem statements.

---

## Quick format selection

| You have…                   | Format  | Jump to                    |
| --------------------------- | ------- | -------------------------- |
| `.csv`, `.tsv`              | CSV     | [CSV](#csv)                |
| `.parquet`, `.parq`         | Parquet | [Parquet](#parquet)        |
| `.json`, `.jsonl`, `.ndjson`| JSON    | [JSON / JSONL](#json--jsonl)|
| `.txt`, `.text`, `.corpus`  | Text    | [TXT](#txt--plain-text)    |
| `.sqlite`, `.db`, `.sqlite3`| SQLite  | [SQLite](#sqlite)          |
| `.log`, app logs            | Log     | [Log files](#log-files)    |

---

## Universal first steps

Before loading any file, run a quick sanity check:

```bash
# Size, line count, first bytes
ls -lh <file>
wc -l <file>          # line count (skip for binary formats)
file <file>           # magic-byte format detection
head -c 512 <file>    # first 512 bytes
```

Then check which libraries are available:

```bash
python - <<'EOF'
import importlib
for lib in ["pandas","pyarrow","polars","sqlite3","jsonlines","datasets"]:
    ok = importlib.util.find_spec(lib) is not None
    print(f"{'✓' if ok else '✗'} {lib}")
EOF
```

Install anything missing before proceeding:

```bash
pip install pandas pyarrow          # baseline — covers most formats
pip install polars                  # optional: faster for large files
pip install jsonlines               # optional: JSONL streaming
pip install datasets                # optional: HuggingFace datasets
```

For a quick automated inspection — format detection, row count, columns,
dtypes, nulls, and a preview — run the bundled script:

```bash
python scripts/inspect.py <filepath>
```

---

## CSV

**Common extensions:** `.csv`, `.tsv`, `.txt` (tabular)

### Load

```python
import pandas as pd

# Auto-detect separator, handle quoted fields
df = pd.read_csv(
    "data.csv",
    sep=None,            # let pandas sniff the delimiter
    engine="python",
    encoding="utf-8",
    on_bad_lines="warn", # skip malformed rows rather than crashing
)
print(df.shape, df.dtypes)
print(df.head())
```

### Profile

```python
# Quick schema + null audit — essential before any ML pipeline
print(df.info())
print(df.describe(include="all"))
print("\nNull counts:\n", df.isnull().sum())
print("\nDuplicate rows:", df.duplicated().sum())
```

### Gotchas

- **Mixed types in a column**: pandas infers types from the first N rows. Pass
  `dtype=str` then cast explicitly if columns contain mixed numeric/string
  entries (common in raw survey data).
- **Encoding errors**: try `encoding="latin-1"` or `encoding="cp1252"` if
  `utf-8` raises `UnicodeDecodeError`.
- **Large CSV files (>1 GB)**: chunk-read or switch to Polars:

  ```python
  # Chunked pandas
  chunks = pd.read_csv("big.csv", chunksize=50_000)
  df = pd.concat(chunks, ignore_index=True)

  # Or Polars (much faster for large files)
  import polars as pl
  df = pl.read_csv("big.csv")
  ```

- **TSV**: pass `sep="\t"` explicitly for tab-separated files.

---

## Parquet

**Common extensions:** `.parquet`, `.parq`

Parquet is the standard columnar format for ML feature stores, Spark
pipelines, and HuggingFace datasets. It preserves dtypes exactly — no
re-casting required.

### Load

```python
import pandas as pd

df = pd.read_parquet("data.parquet")   # uses pyarrow by default
print(df.shape, df.dtypes)
print(df.head())
```

### Inspect schema without loading all data

```python
import pyarrow.parquet as pq

meta = pq.read_metadata("data.parquet")
schema = pq.read_schema("data.parquet")

print(f"Rows: {meta.num_rows:,}  |  Row groups: {meta.num_row_groups}")
print(schema)
```

### Read only selected columns (saves memory)

```python
df = pd.read_parquet("data.parquet", columns=["feature_a", "label"])
```

### Partitioned datasets (directories)

```python
import pyarrow.dataset as ds

dataset = ds.dataset("data/", format="parquet")
# Lazy scan — inspect schema without loading
print(dataset.schema)
# Load into pandas
df = dataset.to_table().to_pandas()
```

### Gotchas

- **`pyarrow` not installed**: `pip install pyarrow`. Alternatively use
  `engine="fastparquet"` with `pip install fastparquet`.
- **Nested columns** (structs/lists): use
  `pyarrow.parquet.read_table().to_pandas(split_blocks=True)` or flatten
  with `pd.json_normalize` after extraction.
- **Large partitioned datasets**: use `pyarrow.dataset` with pushdown
  filters rather than loading everything into memory.

---

## JSON / JSONL

**Common extensions:** `.json`, `.jsonl`, `.ndjson`

Two distinct formats:

| Format | Structure | When used |
|--------|-----------|-----------|
| JSON   | Single object or array in one file | Config, small datasets |
| JSONL  | One JSON object per line | Streaming logs, LLM fine-tuning data, large corpora |

### Load JSON (array of records)

```python
import pandas as pd
import json

# pandas auto-handles top-level arrays
df = pd.read_json("data.json", orient="records")
print(df.shape)
print(df.head())
```

### Load nested / irregular JSON

```python
with open("data.json") as f:
    raw = json.load(f)

# Flatten one level of nesting
df = pd.json_normalize(raw, sep="_")
print(df.columns.tolist())
```

### Load JSONL (one record per line)

```python
import pandas as pd

# pandas handles JSONL natively
df = pd.read_json("data.jsonl", lines=True)
print(df.shape)
```

### Stream large JSONL without loading everything

```python
import json

with open("large.jsonl") as f:
    for i, line in enumerate(f):
        record = json.loads(line)
        # process record
        if i >= 5:
            break   # inspect first N records
```

### HuggingFace fine-tuning format

JSONL files for LLM fine-tuning typically use this schema:

```json
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

Validate the schema before training:

```python
import json

required_roles = {"user", "assistant"}
with open("finetune.jsonl") as f:
    for i, line in enumerate(f):
        ex = json.loads(line)
        roles = {m["role"] for m in ex.get("messages", [])}
        if not required_roles.issubset(roles):
            print(f"Line {i}: missing required roles — got {roles}")
```

### Gotchas

- **`ValueError: Trailing data`** on `.json` files: the file is likely JSONL.
  Switch to `lines=True`.
- **Deeply nested JSON** (3+ levels): `json_normalize` with `record_path`
  and `meta` arguments; see
  [references/json-normalize.md](references/json-normalize.md).
- **Large JSON arrays**: stream with `ijson` (`pip install ijson`) to avoid
  loading the entire array into memory.

---

## TXT / Plain Text

**Common extensions:** `.txt`, `.text`, `.corpus`, `.tok`

Used for raw text corpora, pre-tokenized text, or unstructured notes. The
loading strategy depends on the downstream task.

### Load as a single string

```python
with open("corpus.txt", encoding="utf-8") as f:
    text = f.read()

print(f"Characters: {len(text):,}")
print(f"Words (approx): {len(text.split()):,}")
print(text[:500])
```

### Load as a list of lines (sentence-per-line corpora)

```python
with open("corpus.txt", encoding="utf-8") as f:
    lines = [line.rstrip("\n") for line in f if line.strip()]

print(f"Non-empty lines: {len(lines):,}")
print(lines[:5])
```

### Load into a pandas DataFrame (for NLP tasks)

```python
import pandas as pd

df = pd.read_csv(
    "corpus.txt",
    header=None,
    names=["text"],
    sep="\t",          # adjust if columns exist
    on_bad_lines="warn",
)
print(df.shape)
print(df.head())
```

### Load into HuggingFace datasets

```python
from datasets import load_dataset

ds = load_dataset("text", data_files={"train": "corpus.txt"})
print(ds)
print(ds["train"][0])
```

### Quick vocabulary / token statistics

```python
from collections import Counter
import re

tokens = re.findall(r"\b\w+\b", text.lower())
vocab = Counter(tokens)
print(f"Vocab size: {len(vocab):,}")
print("Top 10:", vocab.most_common(10))
```

### Gotchas

- **Encoding issues**: try `errors="replace"` on `open()` as a last resort;
  inspect with `chardet` (`pip install chardet`):

  ```python
  import chardet
  with open("file.txt", "rb") as f:
      result = chardet.detect(f.read(100_000))
  print(result)
  ```

- **Binary / mixed content**: `file <path>` first to confirm it is actually
  plain text and not a misnamed binary.
- **Very large text files**: use line-by-line iteration rather than
  `f.read()` to avoid OOM.

---

## SQLite

**Common extensions:** `.sqlite`, `.db`, `.sqlite3`

SQLite is a self-contained relational database — common for structured
experiment tracking, annotation stores, and lightweight feature stores.

### Inspect schema (no external library needed)

```python
import sqlite3

conn = sqlite3.connect("data.db")
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]
print("Tables:", tables)

# Schema for each table
for table in tables:
    cursor.execute(f"PRAGMA table_info('{table}');")
    cols = cursor.fetchall()
    print(f"\n{table}:")
    for col in cols:
        print(f"  {col[1]} ({col[2]})")

conn.close()
```

### Load a table into pandas

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect("data.db")
df = pd.read_sql_query("SELECT * FROM my_table LIMIT 10000;", conn)
conn.close()

print(df.shape)
print(df.head())
```

### Query with filters (efficient — avoid loading whole table)

```python
query = """
    SELECT feature_a, feature_b, label
    FROM samples
    WHERE split = 'train'
      AND label IS NOT NULL
    LIMIT 50000;
"""
df = pd.read_sql_query(query, conn)
```

### Row count without loading

```python
cursor.execute("SELECT COUNT(*) FROM my_table;")
print("Rows:", cursor.fetchone()[0])
```

### Gotchas

- **Database locked error**: another process (Jupyter, VS Code SQLite
  viewer) may have the file open. Close other connections first.
- **Read-only databases**: open with `uri=True`:

  ```python
  conn = sqlite3.connect("file:data.db?mode=ro", uri=True)
  ```

- **Large tables**: always push filters into SQL rather than loading the
  full table and filtering in pandas.
- **SQLite doesn't enforce types**: columns declared `INTEGER` may contain
  strings. Always `.dtypes` after loading and cast explicitly.

---

## Log Files

**Common extensions:** `.log`, `.out`, `.err`, application-specific

Logs appear in ML workflows as training logs, inference logs, system
metrics, and experiment outputs. Parsing strategy depends on structure.

### Identify log structure first

```bash
head -30 app.log          # inspect format
grep -c "" app.log        # total line count
```

Common structures:

| Pattern | Example |
|---------|---------|
| Structured (JSON) | `{"time":"...","level":"INFO","msg":"..."}` |
| Semi-structured | `2024-01-01 12:00:00 INFO epoch=1 loss=0.42` |
| Unstructured | `Training complete.` |

### Parse JSON log lines

```python
import json
import pandas as pd

records = []
with open("training.log") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            pass  # skip non-JSON lines

df = pd.DataFrame(records)
print(df.columns.tolist())
print(df.head())
```

### Parse semi-structured logs with regex

```python
import re
import pandas as pd

# Example: "2024-01-01 12:00:05 INFO epoch=3 loss=0.182 acc=0.943"
pattern = re.compile(
    r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+"
    r"(?P<level>\w+)\s+"
    r"epoch=(?P<epoch>\d+)\s+"
    r"loss=(?P<loss>[\d.]+)\s+"
    r"acc=(?P<acc>[\d.]+)"
)

records = []
with open("training.log") as f:
    for line in f:
        m = pattern.search(line)
        if m:
            records.append(m.groupdict())

df = pd.DataFrame(records)
df["epoch"] = df["epoch"].astype(int)
df["loss"] = df["loss"].astype(float)
df["acc"] = df["acc"].astype(float)
print(df.tail(10))
```

### Extract key metrics from training logs

```python
# Plot loss curve directly from log data
import matplotlib.pyplot as plt

plt.plot(df["epoch"], df["loss"], label="loss")
plt.plot(df["epoch"], df["acc"], label="accuracy")
plt.xlabel("Epoch")
plt.legend()
plt.tight_layout()
plt.savefig("training_curve.png")
print("Saved training_curve.png")
```

### Gotchas

- **Mixed JSON and plaintext lines**: always wrap `json.loads` in
  `try/except` and skip non-JSON lines rather than crashing.
- **Very large logs (>500 MB)**: stream line-by-line; never `f.read()` the
  whole file.
- **Timestamps**: parse with `pd.to_datetime(df["timestamp"])` after
  loading for time-series operations.
- **Log rotation** (multiple `.log.1`, `.log.2` files): concatenate in
  order before analysis.

---

## After loading — universal next steps

Once any file is loaded into a DataFrame or data structure:

1. **Audit nulls and types**

   ```python
   print(df.isnull().sum())
   print(df.dtypes)
   ```

2. **Check class balance** (classification problems)

   ```python
   print(df["label"].value_counts(normalize=True))
   ```

3. **Check for data leakage** — confirm train/val/test splits are present
   and mutually exclusive before any feature engineering.

4. **Save a clean intermediate copy**

   ```python
   df.to_parquet("data_clean.parquet", index=False)
   ```

For deeper guidance on each format, see the reference files:

- [references/format-cheatsheet.md](references/format-cheatsheet.md) —
  one-page format comparison table
- [references/large-file-strategies.md](references/large-file-strategies.md) —
  chunking, streaming, and memory-mapped loading for files > 1 GB
- [scripts/inspect.py](scripts/inspect.py) —
  quick CLI to detect format, print row count, columns, dtypes, nulls,
  and a preview
