"""Render the built .docx to PDF and page images, so layout can be checked.

The page limit is a hard submission constraint, and python-docx cannot paginate:
only a real renderer knows where the pages break. This drives the installed Word
to export a PDF, reports the page count, and rasterises each page so the layout
(figure sizes, column balance, orphaned captions) can actually be inspected.

Windows + Microsoft Word only. Read-only with respect to the .docx.

Run:  python preview.py [path-to-docx]
"""

from __future__ import annotations

import pathlib
import sys

WD_FORMAT_PDF = 17
WD_STATISTIC_PAGES = 2


def export_pdf(docx_path: pathlib.Path, pdf_path: pathlib.Path | None = None) -> tuple[pathlib.Path, int]:
    """Export to PDF via Word and return (pdf_path, page_count)."""
    import win32com.client

    docx_path = pathlib.Path(docx_path).resolve()
    pdf_path = pathlib.Path(pdf_path or docx_path.with_suffix(".pdf")).resolve()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)   # Word will not create it

    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    try:
        doc = word.Documents.Open(str(docx_path), ReadOnly=True, AddToRecentFiles=False)
        try:
            doc.Repaginate()
            pages = int(doc.ComputeStatistics(WD_STATISTIC_PAGES))
            doc.SaveAs2(str(pdf_path), FileFormat=WD_FORMAT_PDF)
        finally:
            doc.Close(SaveChanges=False)
    finally:
        word.Quit()
    return pdf_path, pages


def render_pages(pdf_path: pathlib.Path, out_dir: pathlib.Path, dpi: int = 110) -> list[pathlib.Path]:
    """Rasterise every PDF page to PNG for visual inspection."""
    import pymupdf

    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    with pymupdf.open(str(pdf_path)) as doc:
        for i, page in enumerate(doc, start=1):
            dest = out_dir / f"page{i}.png"
            page.get_pixmap(dpi=dpi).save(str(dest))
            written.append(dest)
    return written


def main(docx_path: str, out_dir: str | None = None) -> None:
    docx_path = pathlib.Path(docx_path)
    out_dir = pathlib.Path(out_dir or docx_path.parent / "preview")
    pdf_path, pages = export_pdf(docx_path, out_dir / (docx_path.stem + ".pdf"))
    print(f"Pages: {pages}")
    for p in render_pages(pdf_path, out_dir):
        print(f"  {p}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: python preview.py <docx> [out_dir]")
    main(*sys.argv[1:3])
