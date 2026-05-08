# Large File Strategies

For files that exceed available RAM or take unacceptably long to load.
Rule of thumb: if the file is > 25% of available RAM, use one of these strategies.

---

## Check available memory first

```python
import psutil
ram_gb = psutil.virtual_memory().available / 1e9
print(f"Available RAM: {ram_gb:.1f} GB")
```

---

## CSV — chunked loading

```python
import pandas as pd

chunksize = 100_000
chunks = []
for chunk in pd.read_csv("big.csv", chunksize=chunksize):
    # Optionally filter/aggregate per chunk before concatenating
    chunk = chunk[chunk["label"].notna()]
    chunks.append(chunk)

df = pd.concat(chunks, ignore_index=True)
print(f"Loaded {len(df):,} rows")
```

For aggregation over a large CSV without ever loading all rows:

```python
totals = {}
for chunk in pd.read_csv("big.csv", chunksize=100_000):
    for col in ["revenue", "clicks"]:
        totals[col] = totals.get(col, 0) + chunk[col].sum()
print(totals)
```

---

## Parquet — column and row-group pruning

```python
import pyarrow.dataset as ds
import pyarrow.compute as pc

dataset = ds.dataset("data.parquet", format="parquet")

# Push filters into the scan — only reads matching row groups
table = dataset.to_table(
    columns=["feature_a", "label"],
    filter=pc.field("split") == "train",
)
df = table.to_pandas()
```

---

## JSONL — line-by-line streaming

```python
import json

def stream_jsonl(path, max_rows=None):
    with open(path) as f:
        for i, line in enumerate(f):
            if max_rows and i >= max_rows:
                break
            yield json.loads(line)

# Process without loading everything
for record in stream_jsonl("big.jsonl", max_rows=10_000):
    pass  # your logic here
```

For random-access into a large JSONL, build a byte-offset index:

```python
import json

def build_index(path):
    offsets = []
    with open(path, "rb") as f:
        while True:
            offsets.append(f.tell())
            line = f.readline()
            if not line:
                break
    return offsets

def read_record(path, offsets, idx):
    with open(path, "rb") as f:
        f.seek(offsets[idx])
        return json.loads(f.readline())
```

---

## SQLite — paginated queries

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect("data.db")
page_size = 50_000
offset = 0
frames = []

while True:
    chunk = pd.read_sql_query(
        f"SELECT * FROM samples LIMIT {page_size} OFFSET {offset};",
        conn,
    )
    if chunk.empty:
        break
    frames.append(chunk)
    offset += page_size

df = pd.concat(frames, ignore_index=True)
conn.close()
```

---

## TXT — memory-mapped reading

```python
import mmap

with open("huge_corpus.txt", "rb") as f:
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    # Seek to a specific byte position instantly
    mm.seek(1_000_000)
    snippet = mm.read(1024).decode("utf-8", errors="replace")
    print(snippet)
    mm.close()
```

---

## Universal fallback — Polars lazy API

Polars supports lazy query planning across all common formats:

```python
import polars as pl

# CSV
q = pl.scan_csv("big.csv")

# Parquet (also works on directories)
q = pl.scan_parquet("data/*.parquet")

# JSONL
q = pl.scan_ndjson("big.jsonl")

# Apply transformations lazily, then collect only what you need
result = (
    q
    .filter(pl.col("label").is_not_null())
    .select(["feature_a", "feature_b", "label"])
    .collect()
)
print(result.shape)
```

Polars automatically parallelizes the scan across CPU cores and only
reads the columns you select from Parquet files.
