---
name: literature-db
description: >
  Store, index, and semantically search a local corpus of research papers using
  a LanceDB vector database with FlashRank re-ranking. Use this skill for large
  (200+ paper) literature-review sessions where you need to insert paper
  metadata and text, then retrieve the most relevant passages for a query. Runs
  fully local and server-less (ONNX Runtime on CPU). Trigger when the user asks
  to build a paper database, remember/index papers, or "search my papers" for a
  specific topic.
license: MIT
compatibility: opencode
---

# Literature Database (LanceDB + FlashRank)

A local, zero-server semantic store for research literature. Embeddings
(`bge-small-en-v1.5`, 384-dim) and re-ranking (`ms-marco-MiniLM-L-6-v2`) both
run in-process via ONNX Runtime on CPU — no Ollama, llama.cpp, or background
model server is required. Each invocation loads the model, does its work,
prints JSON, and exits.

Primary users: `@research-analyst` and `@doc-analyzer`.

## When to use

- Building a searchable corpus during a multi-paper literature review.
- Re-finding the exact passage that supports a claim across dozens of papers.
- When naive full-text reads would overflow the context window.

Do **not** use for a one-off single-paper question — read the paper directly.

## Prerequisites

- **`uv`** must be installed and on PATH. The backend script
  `scripts/literature_db.py` declares its own dependencies via PEP 723 inline
  metadata (`lancedb`, `fastembed`, `flashrank`, `pyarrow`, `numpy`), so
  `uv run --script` resolves them into an isolated environment on first run.
- First run downloads the embedding + re-ranking models to the local cache
  (~40 MB) and the Python deps. Subsequent runs are fast (~100 ms model load).

## Interfaces

There are two equivalent entry points. Prefer the native tool inside OpenCode.

### 1. Native OpenCode tool: `literature_db`

| arg            | type     | notes                                             |
| -------------- | -------- | ------------------------------------------------- |
| `action`       | enum     | `init` \| `insert` \| `search` \| `index_pdf`     |
| `query`        | string?  | search text (for `action: search`)                |
| `topK`         | number?  | candidates before re-ranking (default 20)         |
| `filePath`     | string?  | Markdown/text paper file (for `action: insert`)   |
| `jsonFile`     | string?  | JSON file of paper(s) (for `action: insert`)      |
| `metadataJson` | string?  | JSON metadata string, paired with `filePath`      |

`search` returns the top 5 re-ranked passages as JSON.

### 2. CLI (equivalent, for scripting / debugging)

```bash
# Initialize the table (idempotent).
uv run --script scripts/literature_db.py init

# Insert a batch of papers from a JSON file.
uv run --script scripts/literature_db.py insert --json_file papers.json

# Insert a single Markdown paper with inline metadata.
uv run --script scripts/literature_db.py insert \
  --file_path paper.md --metadata '{"title":"...","doi":"...","authors":["A. B."]}'

# Search (retrieve 20 candidates, re-rank, return top 5).
uv run --script scripts/literature_db.py search --query "graph attention networks" --top_k 20 --rerank
```

## Input formats

**JSON file** (`--json_file`): either a single object, a list of objects, or
`{"papers": [ ... ]}`. Each paper object may contain:

```json
{
  "id": "2305.10601",
  "title": "Tree of Thoughts",
  "authors": ["Shunyu Yao", "..."],
  "published_date": "2023-05-17",
  "abstract": "…",
  "text": "full body text to chunk and embed …",
  "doi": "",
  "pmid": "",
  "arxiv_id": "2305.10601"
}
```

Body text for embedding is taken from the first present of
`chunk_text` / `text` / `body` / `content` / `full_text`, falling back to the
`abstract`. Text is split into overlapping ~1200-character chunks; each chunk
becomes its own vector row sharing the paper's metadata.

**Markdown/text file** (`--file_path`): the file contents are the body text;
`--metadata` (or `--metadata_file`) supplies the metadata fields. If no title
is given, the filename is used.

## Output (search)

```json
{
  "status": "success",
  "action": "search",
  "query": "…",
  "reranked": true,
  "candidates_considered": 20,
  "results": [
    {
      "id": "2305.10601#chunk3",
      "title": "Tree of Thoughts",
      "authors": ["Shunyu Yao", "…"],
      "chunk_text": "…the most relevant passage…",
      "rerank_score": 8.42,
      "vector_distance": 0.19,
      "doi": "", "pmid": "", "arxiv_id": "2305.10601"
    }
  ]
}
```

Cite the papers (title + id/doi/arxiv_id) surfaced in `results` when using them.

## Notes & limitations

- **PDF indexing is not supported in this version.** Convert PDFs to
  Markdown/text first, then `insert --file_path`.
- The database is stored at `.literature_db/` under the opencode config root
  and is git-ignored.
- `stdout` is always a single JSON document; all progress/warnings go to
  `stderr`, so the tool output is safe to parse directly.
