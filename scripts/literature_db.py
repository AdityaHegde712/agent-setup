# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "lancedb",
#   "fastembed",
#   "flashrank",
#   "pyarrow",
#   "numpy",
# ]
# ///
"""Local literature database: LanceDB vector store + FlashRank re-ranking.

Zero-server design. Both embedding (`fastembed` / `bge-small-en-v1.5`) and
re-ranking (`flashrank` / `ms-marco-MiniLM-L-6-v2`) run in-process via ONNX
Runtime CPU binaries. There is NO background model server: this script loads
the models, does its work, prints one JSON document to stdout, and exits.

Run through uv so the inline dependencies above are resolved into an isolated
environment (this ignores the surrounding project's pyproject.toml):

    uv run --script scripts/literature_db.py init
    uv run --script scripts/literature_db.py insert --json_file papers.json
    uv run --script scripts/literature_db.py insert --file_path paper.md --metadata '{...}'
    uv run --script scripts/literature_db.py search --query "text" --top_k 20 --rerank

IMPORTANT: stdout carries ONLY the final JSON result. All progress/diagnostic
output (model downloads, warnings) is redirected to stderr so callers can parse
stdout directly.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys

# Silence library progress bars so nothing leaks onto stdout/stderr noisily.
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TQDM_DISABLE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

VECTOR_DIM = 384  # bge-small-en-v1.5 output dimension
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
# NOTE: The original spec named "ms-marco-MiniLM-L-6-v2", but that model is not
# present in the installed flashrank's model map and its download URL 404s.
# ms-marco-MiniLM-L-12-v2 is the available MiniLM cross-encoder (quantized ONNX,
# ~34MB) chosen as the substitute.
RERANK_MODEL = "ms-marco-MiniLM-L-12-v2"
TABLE_NAME = "papers"

# The database lives next to the opencode config root (parent of scripts/).
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_ROOT = os.path.dirname(_SCRIPT_DIR)
DB_PATH = os.path.join(_CONFIG_ROOT, ".literature_db")


@contextlib.contextmanager
def _stdout_to_stderr():
    """Temporarily redirect stdout to stderr.

    Some third-party libraries (model loaders, ORT) may print to stdout on
    first run. We route that to stderr so the caller's stdout stays clean JSON.
    """
    old = sys.stdout
    sys.stdout = sys.stderr
    try:
        yield
    finally:
        sys.stdout = old


def _emit(payload: dict) -> None:
    """Print exactly one JSON document to the real stdout."""
    sys.stdout.write(json.dumps(payload, indent=2))
    sys.stdout.write("\n")
    sys.stdout.flush()


# --------------------------------------------------------------------------- #
# Lazy, cached model + db handles                                             #
# --------------------------------------------------------------------------- #
_EMBEDDER = None
_RANKER = None


def _get_embedder():
    global _EMBEDDER
    if _EMBEDDER is None:
        from fastembed import TextEmbedding

        with _stdout_to_stderr():
            _EMBEDDER = TextEmbedding(model_name=EMBED_MODEL)
    return _EMBEDDER


def _get_ranker():
    global _RANKER
    if _RANKER is None:
        from flashrank import Ranker

        with _stdout_to_stderr():
            _RANKER = Ranker(model_name=RERANK_MODEL)
    return _RANKER


def _embed(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts into 384-dim float vectors."""
    embedder = _get_embedder()
    with _stdout_to_stderr():
        vectors = list(embedder.embed(texts))
    return [[float(x) for x in vec] for vec in vectors]


def _schema():
    import pyarrow as pa

    return pa.schema(
        [
            ("id", pa.string()),
            ("title", pa.string()),
            ("authors", pa.string()),  # JSON-encoded string array
            ("published_date", pa.string()),
            ("abstract", pa.string()),
            ("chunk_text", pa.string()),
            ("doi", pa.string()),
            ("pmid", pa.string()),
            ("arxiv_id", pa.string()),
            ("vector", pa.list_(pa.float32(), VECTOR_DIM)),
        ]
    )


def _connect():
    import lancedb

    with _stdout_to_stderr():
        return lancedb.connect(DB_PATH)


def _table_names(db) -> list[str]:
    """Return existing table names across lancedb API variations.

    Newer lancedb returns a ``ListTablesResponse`` (with a ``.tables`` attribute)
    from ``list_tables()``; other builds return a plain list from the (now
    deprecated) ``table_names()``. Handle both so table detection is reliable.
    """
    lister = getattr(db, "list_tables", None)
    if lister is not None:
        try:
            res = lister()
        except Exception:
            res = None
        if res is not None:
            tables = getattr(res, "tables", None)
            if tables is not None:
                return list(tables)
            if isinstance(res, (list, tuple)):
                return list(res)
    namer = getattr(db, "table_names", None)
    if namer is not None:
        return list(namer())
    return []


def _open_or_create_table(db):
    """Return the papers table, creating an empty one if it does not exist."""
    with _stdout_to_stderr():
        if TABLE_NAME in _table_names(db):
            return db.open_table(TABLE_NAME)
        return db.create_table(TABLE_NAME, schema=_schema())


# --------------------------------------------------------------------------- #
# Text chunking                                                               #
# --------------------------------------------------------------------------- #
def _chunk_text(text: str, size: int = 1200, overlap: int = 150) -> list[str]:
    """Split text into overlapping character windows on whitespace boundaries."""
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]

    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + size, n)
        # Prefer to break on whitespace so we don't split words.
        if end < n:
            ws = text.rfind(" ", start, end)
            if ws > start + int(size * 0.5):
                end = ws
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return chunks


# --------------------------------------------------------------------------- #
# Metadata normalisation                                                       #
# --------------------------------------------------------------------------- #
def _normalise_paper(meta: dict) -> dict:
    """Coerce arbitrary paper metadata into the table's string fields."""
    authors = meta.get("authors", [])
    if isinstance(authors, str):
        # Could already be a JSON array or a plain comma-separated string.
        try:
            parsed = json.loads(authors)
            authors = parsed if isinstance(parsed, list) else [authors]
        except (ValueError, TypeError):
            authors = [a.strip() for a in authors.split(",") if a.strip()]
    elif not isinstance(authors, list):
        authors = [str(authors)]

    return {
        "id": str(meta.get("id") or meta.get("arxiv_id") or meta.get("doi") or ""),
        "title": str(meta.get("title") or ""),
        "authors": json.dumps(authors),
        "published_date": str(
            meta.get("published_date") or meta.get("published") or ""
        ),
        "abstract": str(meta.get("abstract") or meta.get("summary") or ""),
        "doi": str(meta.get("doi") or ""),
        "pmid": str(meta.get("pmid") or ""),
        "arxiv_id": str(meta.get("arxiv_id") or ""),
    }


def _paper_text(meta: dict, override_text: str | None = None) -> str:
    """Pick the best available body text to chunk & embed."""
    if override_text:
        return override_text
    for key in ("chunk_text", "text", "body", "content", "full_text"):
        val = meta.get(key)
        if val:
            return str(val)
    # Fall back to abstract/summary.
    return str(meta.get("abstract") or meta.get("summary") or meta.get("title") or "")


def _build_rows(meta: dict, override_text: str | None = None) -> list[dict]:
    """Chunk one paper's text and produce embedded rows sharing its metadata."""
    base = _normalise_paper(meta)
    body = _paper_text(meta, override_text)
    chunks = _chunk_text(body)
    if not chunks:
        return []

    vectors = _embed(chunks)
    rows: list[dict] = []
    base_id = base["id"] or f"paper-{abs(hash(base['title'])) % (10**8)}"
    for idx, (chunk, vec) in enumerate(zip(chunks, vectors)):
        row = dict(base)
        row["id"] = f"{base_id}#chunk{idx}"
        row["chunk_text"] = chunk
        row["vector"] = vec
        rows.append(row)
    return rows


# --------------------------------------------------------------------------- #
# Commands                                                                     #
# --------------------------------------------------------------------------- #
def cmd_init(_args) -> int:
    db = _connect()
    with _stdout_to_stderr():
        if TABLE_NAME not in _table_names(db):
            db.create_table(TABLE_NAME, schema=_schema())
    _emit(
        {
            "status": "success",
            "action": "init",
            "db_path": DB_PATH,
            "table": TABLE_NAME,
        }
    )
    return 0


def cmd_insert(args) -> int:
    papers: list[dict] = []
    override_texts: list[str | None] = []

    if args.json_file:
        with open(args.json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            # Support {"papers": [...]} or a single paper object.
            if isinstance(data.get("papers"), list):
                data = data["papers"]
            else:
                data = [data]
        for item in data:
            papers.append(item)
            override_texts.append(None)
    elif args.file_path:
        meta = {}
        if args.metadata:
            meta = json.loads(args.metadata)
        elif args.metadata_file:
            with open(args.metadata_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
        with open(args.file_path, "r", encoding="utf-8", errors="ignore") as f:
            body = f.read()
        if not meta.get("title"):
            meta["title"] = os.path.splitext(os.path.basename(args.file_path))[0]
        papers.append(meta)
        override_texts.append(body)
    else:
        _emit(
            {
                "status": "error",
                "message": "insert requires either --json_file or --file_path.",
            }
        )
        return 1

    all_rows: list[dict] = []
    for meta, text in zip(papers, override_texts):
        all_rows.extend(_build_rows(meta, text))

    if not all_rows:
        _emit(
            {
                "status": "error",
                "message": "No embeddable text found in the provided input.",
            }
        )
        return 1

    db = _connect()
    table = _open_or_create_table(db)
    with _stdout_to_stderr():
        table.add(all_rows)

    _emit(
        {
            "status": "success",
            "action": "insert",
            "papers_inserted": len(papers),
            "chunks_inserted": len(all_rows),
            "db_path": DB_PATH,
        }
    )
    return 0


def cmd_search(args) -> int:
    if not args.query:
        _emit({"status": "error", "message": "search requires --query."})
        return 1

    db = _connect()
    with _stdout_to_stderr():
        if TABLE_NAME not in _table_names(db):
            table = None
        else:
            table = db.open_table(TABLE_NAME)

    if table is None:
        _emit(
            {
                "status": "success",
                "action": "search",
                "query": args.query,
                "results": [],
                "message": "Database not initialized or empty. Run `init`/`insert` first.",
            }
        )
        return 0

    top_k = args.top_k or 20
    query_vec = _embed([args.query])[0]

    with _stdout_to_stderr():
        candidates = table.search(query_vec).limit(top_k).to_list()

    if not candidates:
        _emit(
            {
                "status": "success",
                "action": "search",
                "query": args.query,
                "results": [],
            }
        )
        return 0

    ranked = candidates
    if args.rerank and candidates:
        from flashrank import RerankRequest

        passages = [
            {
                "id": i,
                "text": c.get("chunk_text", ""),
                "meta": c,
            }
            for i, c in enumerate(candidates)
        ]
        ranker = _get_ranker()
        with _stdout_to_stderr():
            reranked = ranker.rerank(RerankRequest(query=args.query, passages=passages))
        # flashrank returns passages sorted by descending relevance score.
        ranked = []
        for r in reranked:
            item = dict(r["meta"])
            item["rerank_score"] = float(r.get("score", 0.0))
            ranked.append(item)

    def _format(row: dict) -> dict:
        authors = row.get("authors", "[]")
        try:
            authors = json.loads(authors)
        except (ValueError, TypeError):
            pass
        return {
            "id": row.get("id", ""),
            "title": row.get("title", ""),
            "authors": authors,
            "published_date": row.get("published_date", ""),
            "chunk_text": row.get("chunk_text", ""),
            "abstract": row.get("abstract", ""),
            "doi": row.get("doi", ""),
            "pmid": row.get("pmid", ""),
            "arxiv_id": row.get("arxiv_id", ""),
            "vector_distance": row.get("_distance"),
            "rerank_score": row.get("rerank_score"),
        }

    results = [_format(r) for r in ranked[:5]]
    _emit(
        {
            "status": "success",
            "action": "search",
            "query": args.query,
            "reranked": bool(args.rerank),
            "candidates_considered": len(candidates),
            "results": results,
        }
    )
    return 0


def cmd_index_pdf(_args) -> int:
    _emit(
        {
            "status": "error",
            "action": "index_pdf",
            "message": (
                "PDF indexing is not supported in this version. Convert the PDF "
                "to Markdown/text first (see scripts/html_to_md.py or a PDF-to-text "
                "step) and use `insert --file_path <file.md> --metadata '{...}'`."
            ),
        }
    )
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local literature vector database.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Initialize the LanceDB table.")

    p_ins = sub.add_parser("insert", help="Insert paper(s) with auto-embeddings.")
    p_ins.add_argument("--json_file", help="Path to a JSON file of paper(s).")
    p_ins.add_argument("--file_path", help="Path to a Markdown/text paper file.")
    p_ins.add_argument("--metadata", help="Inline JSON string of paper metadata.")
    p_ins.add_argument("--metadata_file", help="Path to a JSON metadata file.")

    p_srch = sub.add_parser("search", help="Vector search with optional re-ranking.")
    p_srch.add_argument("--query", help="Search query text.")
    p_srch.add_argument(
        "--top_k", type=int, default=20, help="Candidates to retrieve (default 20)."
    )
    p_srch.add_argument(
        "--rerank", action="store_true", help="Re-rank candidates with FlashRank."
    )

    # index_pdf is exposed by the OpenCode tool; keep a matching subcommand.
    p_pdf = sub.add_parser("index_pdf", help="(Unsupported) index a PDF file.")
    p_pdf.add_argument("--file_path")
    p_pdf.add_argument("--metadata")

    return parser


def main() -> int:
    args = build_parser().parse_args()
    handlers = {
        "init": cmd_init,
        "insert": cmd_insert,
        "search": cmd_search,
        "index_pdf": cmd_index_pdf,
    }
    handler = handlers.get(args.command)
    if handler is None:
        _emit({"status": "error", "message": f"Unknown command: {args.command}"})
        return 1
    try:
        return handler(args)
    except Exception as exc:  # noqa: BLE001 - surface a clean JSON error
        _emit({"status": "error", "message": f"{type(exc).__name__}: {exc}"})
        return 1


if __name__ == "__main__":
    sys.exit(main())
