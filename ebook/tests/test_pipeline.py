import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from pista.checks import validate_manuscript
from pista.epub import compile_epub
from pista.markdown import parse_markdown, to_xhtml
from pista.pdf import compile_pdf
from pista.rag import build_index, search

ROOT = Path(__file__).resolve().parents[1]


class MarkdownTests(unittest.TestCase):
    def test_preserves_ordered_lists_tables_quotes_and_links(self):
        source = """# Título

1. Primeiro
2. Segundo

| Campo | Valor |
|---|---|
| A | B |

> Uma frase

[Fonte](https://example.com/a?x=1&y=2)
"""
        blocks = parse_markdown(source)
        kinds = [block["type"] for block in blocks]
        self.assertIn("ol", kinds)
        self.assertIn("table", kinds)
        self.assertIn("quote", kinds)
        self.assertIn("<ol>", to_xhtml(source))
        self.assertIn("https://example.com/a?x=1&amp;y=2", to_xhtml(source))


class ManuscriptTests(unittest.TestCase):
    def test_manuscript_meets_sdd_acceptance(self):
        self.assertEqual(validate_manuscript(ROOT), [])

    def test_rag_index_returns_cited_source_and_relevant_section(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sources").mkdir()
            (root / "sources" / "notes.md").write_text("# Feedback\n\nPeça feedback sobre o refrão.", encoding="utf-8")
            build_index(root, root / "data" / "index.json")
            results = search(root, "feedback refrão", 2)
            self.assertTrue(results)
            self.assertEqual(results[0][1]["source"], "sources/notes.md")
            self.assertEqual(results[0][1]["section"], "Feedback")


class BuildTests(unittest.TestCase):
    def test_epub_is_well_formed_and_has_navigation(self):
        with tempfile.TemporaryDirectory() as temp:
            path = compile_epub(ROOT, Path(temp) / "book.epub")
            with zipfile.ZipFile(path) as archive:
                self.assertEqual(archive.read("mimetype"), b"application/epub+zip")
                self.assertEqual(archive.namelist()[0], "mimetype")
                for name in archive.namelist():
                    if name.endswith((".xhtml", ".opf", ".xml", ".svg")):
                        ET.fromstring(archive.read(name))
                nav = archive.read("EPUB/nav.xhtml").decode("utf-8")
                self.assertIn("chapter-09.xhtml", nav)
                cover = archive.read("EPUB/cover.xhtml").decode("utf-8")
                self.assertIn("soundmark.svg", cover)

    def test_pdf_has_page_tree_and_navigable_chapter_links(self):
        with tempfile.TemporaryDirectory() as temp:
            data = compile_pdf(ROOT, Path(temp) / "book.pdf").read_bytes()
            self.assertTrue(data.startswith(b"%PDF-1.7"))
            self.assertIn(b"/Type /Pages", data)
            self.assertIn(b"/Subtype /Link", data)
            self.assertIn(b"/Dest [", data)
            self.assertIn(b"/BaseFont /Times-Bold", data)
            self.assertIn(b"/MediaBox [0 0 419.53 595.28]", data)
            self.assertTrue(data.rstrip().endswith(b"%%EOF"))
            text = data.decode("latin-1")
            xref_offset = int(text.rsplit("startxref\n", 1)[1].splitlines()[0])
            self.assertEqual(text[xref_offset:xref_offset+4], "xref")


if __name__ == "__main__":
    unittest.main()
