from pathlib import Path
import pytest
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


def create_sample_pdf(pdf_path: Path) -> None:
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    title = Paragraph("Sample Test Document", styles["Heading1"])
    story.append(title)
    story.append(Spacer(1, 12))

    body = Paragraph("This is a sample paragraph for PDF extraction testing.", styles["Normal"])
    story.append(body)
    story.append(Spacer(1, 12))

    data = [
        ["Header 1", "Header 2", "Header 3"],
        ["Row 1 Col 1", "Row 1 Col 2", "Row 1 Col 3"],
        ["Row 2 Col 1", "Row 2 Col 2", "Row 2 Col 3"]
    ]
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(t)

    doc.build(story)


def test_pdf_extraction(tmp_path: Path) -> None:
    from mcp_servers.pdf_server.server import read_pdf, read_pdf_tables, get_pdf_toc

    sample_pdf = tmp_path / "test_doc.pdf"
    create_sample_pdf(sample_pdf)

    text_result = read_pdf(str(sample_pdf))
    assert "Sample Test Document" in text_result
    assert "sample paragraph" in text_result

    table_result = read_pdf_tables(str(sample_pdf))
    assert "| Header 1 | Header 2 | Header 3 |" in table_result
    assert "| Row 1 Col 1 | Row 1 Col 2 | Row 1 Col 3 |" in table_result

    toc_result = get_pdf_toc(str(sample_pdf))
    assert isinstance(toc_result, str)


def test_file_not_found() -> None:
    from mcp_servers.pdf_server.server import read_pdf, read_pdf_tables, get_pdf_toc

    missing_path = "non_existent_file.pdf"
    with pytest.raises(FileNotFoundError):
        read_pdf(missing_path)

    with pytest.raises(FileNotFoundError):
        read_pdf_tables(missing_path)

    with pytest.raises(FileNotFoundError):
        get_pdf_toc(missing_path)


def test_invalid_page_range(tmp_path: Path) -> None:
    from mcp_servers.pdf_server.server import read_pdf

    sample_pdf = tmp_path / "test_doc.pdf"
    create_sample_pdf(sample_pdf)

    with pytest.raises(ValueError):
        read_pdf(str(sample_pdf), start_page=10, end_page=20)
