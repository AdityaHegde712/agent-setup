import os
from pathlib import Path
import pdfplumber
import pypdf
from mcp.server.mcpserver import MCPServer


mcp = MCPServer("PDF-Tools")


def format_markdown_table(table_data: list[list[str | None]]) -> str:
    if not table_data:
        return ""

    cleaned_data: list[list[str]] = []
    for row in table_data:
        cleaned_row = [str(cell).strip() if cell is not None else "" for cell in row]
        cleaned_data.append(cleaned_row)

    header = cleaned_data[0]
    separator = ["---"] * len(header)
    rows = cleaned_data[1:]

    lines: list[str] = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(separator) + " |"
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def get_cache_path(pdf_path: Path, suffix: str) -> Path:
    parent_dir = pdf_path.parent
    cache_dir = parent_dir / ".cache"

    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / f"{pdf_path.stem}_{suffix}.md"
    except OSError:
        temp_cache = Path(os.environ.get("TEMP", ".")) / ".cache"
        temp_cache.mkdir(parents=True, exist_ok=True)
        return temp_cache / f"{pdf_path.stem}_{suffix}.md"


@mcp.tool()
def read_pdf(file_path: str, start_page: int = 1, end_page: int | None = None) -> str:
    path_obj = Path(file_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    extracted_pages: list[str] = []
    with pdfplumber.open(path_obj) as pdf:
        total_pages = len(pdf.pages)
        last_page = end_page if end_page is not None else total_pages

        is_valid_range = 1 <= start_page <= last_page and start_page <= total_pages
        if not is_valid_range:
            raise ValueError(f"Invalid page range: start_page={start_page}, end_page={end_page}, total={total_pages}")

        for idx in range(start_page - 1, min(last_page, total_pages)):
            page_text = pdf.pages[idx].extract_text() or ""
            extracted_pages.append(f"--- Page {idx + 1} ---\n{page_text}")

    full_content = "\n\n".join(extracted_pages)
    cache_file = get_cache_path(path_obj, "text")

    try:
        cache_file.write_text(full_content, encoding="utf-8")
    except OSError:
        pass

    return full_content


@mcp.tool()
def read_pdf_tables(file_path: str, page_num: int | None = None) -> str:
    path_obj = Path(file_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    formatted_tables: list[str] = []
    with pdfplumber.open(path_obj) as pdf:
        total_pages = len(pdf.pages)
        pages_to_process = [page_num - 1] if page_num is not None else range(total_pages)

        for p_idx in pages_to_process:
            if not (0 <= p_idx < total_pages):
                continue

            tables = pdf.pages[p_idx].extract_tables()
            for t_idx, table in enumerate(tables):
                table_md = format_markdown_table(table)
                if table_md:
                    formatted_tables.append(f"### Page {p_idx + 1} - Table {t_idx + 1}\n{table_md}")

    result_content = "\n\n".join(formatted_tables) if formatted_tables else "No tables found."
    cache_file = get_cache_path(path_obj, "tables")

    try:
        cache_file.write_text(result_content, encoding="utf-8")
    except OSError:
        pass

    return result_content


@mcp.tool()
def get_pdf_toc(file_path: str) -> str:
    path_obj = Path(file_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    reader = pypdf.PdfReader(path_obj)
    outline = reader.outline

    if not outline:
        return "No Table of Contents (outline) found in PDF."

    toc_lines: list[str] = []

    def parse_outline_item(item: list | pypdf.types.Destination, depth: int = 0) -> None:
        if isinstance(item, list):
            for sub_item in item:
                parse_outline_item(sub_item, depth + 1)
            return

        title = getattr(item, "title", str(item))
        indent = "  " * depth
        toc_lines.append(f"{indent}- {title}")

    for element in outline:
        parse_outline_item(element, 0)

    toc_text = "\n".join(toc_lines)
    cache_file = get_cache_path(path_obj, "toc")

    try:
        cache_file.write_text(toc_text, encoding="utf-8")
    except OSError:
        pass

    return toc_text


if __name__ == "__main__":
    mcp.run()
