# `pd.json_normalize` — Flattening Nested JSON

Reference for using `pandas.json_normalize` to handle 2+ levels of nesting
in JSON data, a common pattern in API responses, annotation exports, and
LLM evaluation datasets.

---

## When you need this

`pd.read_json()` works well for flat arrays of records. When your JSON looks
like this instead:

```json
[
  {
    "id": 1,
    "user": {
      "name": "Alice",
      "location": { "city": "Berlin", "country": "DE" }
    },
    "scores": [0.91, 0.87, 0.95],
    "labels": [
      { "tag": "positive", "confidence": 0.91 },
      { "tag": "neutral",  "confidence": 0.09 }
    ]
  }
]
```

`pd.read_json()` will give you columns that contain dicts or lists —
not useful for ML feature matrices. `json_normalize` flattens this properly.

---

## Signature

```python
pandas.json_normalize(
    data,               # dict, list of dicts, or parsed JSON
    record_path=None,   # key (or list of keys) to the nested list to expand
    meta=None,          # parent fields to carry alongside the expanded records
    meta_prefix=None,   # optional prefix for meta column names
    record_prefix=None, # optional prefix for expanded record columns
    sep="_",            # separator for nested key names (default: ".")
    max_level=None,     # max nesting depth to flatten (None = unlimited)
    errors="raise",     # "raise" or "ignore" missing meta keys
)
```

---

## Level 1 — simple nested objects (structs)

Flatten one level of nested dicts into dot-separated column names.

**Input:**
```json
[
  {"id": 1, "user": {"name": "Alice", "age": 30}},
  {"id": 2, "user": {"name": "Bob",   "age": 25}}
]
```

```python
import json
import pandas as pd

with open("data.json") as f:
    raw = json.load(f)

df = pd.json_normalize(raw, sep="_")
# Columns: id | user_name | user_age
print(df.columns.tolist())
# ['id', 'user_name', 'user_age']
print(df)
```

**Use `sep="_"` not `sep="."` for ML pipelines** — dot-separated names break
scikit-learn feature name validation and many other libraries.

---

## Level 2 — deeply nested objects (3+ levels)

Use `max_level` to control how deep the flattening goes.

**Input:**
```json
[
  {
    "id": 1,
    "user": {
      "name": "Alice",
      "location": {"city": "Berlin", "country": "DE"}
    }
  }
]
```

```python
# Flatten everything (default)
df = pd.json_normalize(raw, sep="_")
# Columns: id | user_name | user_location_city | user_location_country

# Flatten only 1 level deep — location stays as a dict column
df = pd.json_normalize(raw, sep="_", max_level=1)
# Columns: id | user_name | user_location
```

---

## Level 3 — nested lists (arrays of records)

This is the most common ML case: a parent record containing a list of
child records (e.g., annotation spans, per-token labels, conversation turns).

Use `record_path` to expand the nested list, and `meta` to carry parent
fields alongside each child row.

**Input:**
```json
[
  {
    "doc_id": "doc_001",
    "text": "The quick brown fox",
    "labels": [
      {"tag": "positive", "confidence": 0.91},
      {"tag": "neutral",  "confidence": 0.09}
    ]
  },
  {
    "doc_id": "doc_002",
    "text": "A rainy day",
    "labels": [
      {"tag": "negative", "confidence": 0.78}
    ]
  }
]
```

```python
df = pd.json_normalize(
    raw,
    record_path="labels",          # expand the 'labels' list
    meta=["doc_id", "text"],       # carry these parent fields into each row
    sep="_",
)

# Result:
#   tag        confidence  doc_id    text
#   positive   0.91        doc_001   The quick brown fox
#   neutral    0.09        doc_001   The quick brown fox
#   negative   0.78        doc_002   A rainy day

print(df)
```

Each label becomes its own row, with `doc_id` and `text` repeated — the
correct "tidy" format for ML training data.

---

## Level 4 — nested lists inside nested objects

Use a list of keys for `record_path` to drill into a deeper path.

**Input:**
```json
[
  {
    "batch_id": "b1",
    "results": {
      "annotations": [
        {"span": [0, 5], "label": "PER"},
        {"span": [6, 11], "label": "ORG"}
      ]
    }
  }
]
```

```python
df = pd.json_normalize(
    raw,
    record_path=["results", "annotations"],  # path as a list of keys
    meta=["batch_id"],
    sep="_",
)
# Columns: span | label | batch_id
```

---

## Common patterns in ML datasets

### HuggingFace-style conversation data

```json
[
  {
    "id": "conv_001",
    "messages": [
      {"role": "user",      "content": "Hello"},
      {"role": "assistant", "content": "Hi there!"}
    ]
  }
]
```

```python
df = pd.json_normalize(
    raw,
    record_path="messages",
    meta=["id"],
    record_prefix="msg_",   # avoids name collision if parent also has 'role'
)
# Columns: msg_role | msg_content | id
```

### Nested evaluation results

```json
[
  {
    "model": "gpt-4",
    "metrics": {"bleu": 0.42, "rouge": {"r1": 0.61, "r2": 0.38}}
  }
]
```

```python
df = pd.json_normalize(raw, sep="_")
# Columns: model | metrics_bleu | metrics_rouge_r1 | metrics_rouge_r2
```

---

## Handling missing keys

If some records are missing a field that others have, `json_normalize`
fills with `NaN` by default. For `meta` fields, use `errors="ignore"` to
suppress `KeyError` when a parent field is absent in some records:

```python
df = pd.json_normalize(
    raw,
    record_path="labels",
    meta=["doc_id", "source"],  # 'source' might be absent in some records
    errors="ignore",            # fill with NaN instead of raising
    sep="_",
)
```

---

## Gotchas

- **`record_path` only works on list-valued fields.** If the nested value is
  a dict (not a list), just use `sep` flattening — no `record_path` needed.
- **Mixed-type arrays** (some records have a list, others have `null`):
  filter out null records before normalizing, or use `errors="ignore"`.
- **Very deeply nested data** (5+ levels): consider flattening level by level
  in stages, or use `jmespath` (`pip install jmespath`) to extract only the
  paths you actually need before calling `json_normalize`.
- **Column name collisions**: if a parent `meta` field has the same name as
  a child `record_path` field, use `meta_prefix` or `record_prefix` to
  disambiguate.
- **Performance on large arrays**: `json_normalize` loads everything into
  memory. For JSONL files with millions of records, stream and normalize in
  batches:

  ```python
  import json
  import pandas as pd

  batch, batch_size = [], 10_000
  frames = []

  with open("large.jsonl") as f:
      for line in f:
          batch.append(json.loads(line))
          if len(batch) >= batch_size:
              frames.append(pd.json_normalize(batch, record_path="labels", meta=["id"], sep="_"))
              batch = []
      if batch:
          frames.append(pd.json_normalize(batch, record_path="labels", meta=["id"], sep="_"))

  df = pd.concat(frames, ignore_index=True)
  ```
