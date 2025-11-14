# site_tools.py
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List

ALLOWED_EXT = {".html", ".css", ".js", ".tsx", ".ts", ".jsx", ".json"}


def load_existing_files(root: Path) -> Dict[str, str]:
    """
    Load existing project files into a dict: { 'relative/path': 'content' }.
    Only picks web-related files (html, css, js, etc.).
    """
    files: Dict[str, str] = {}
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in ALLOWED_EXT:
            rel = path.relative_to(root).as_posix()
            try:
                files[rel] = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
    return files


def summarize_files_for_manager(files: Dict[str, str]) -> Dict[str, dict]:
    """Summarize files without sending full code back every time."""
    summary: Dict[str, dict] = {}
    for name, content in files.items():
        summary[name] = {
            "length": len(content),
            "preview": content[:200],
        }
    return summary


class _SimpleHTMLAnalyzer(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title: str | None = None
        self._current_tag: str | None = None
        self.headings: List[dict] = []
        self.links: List[dict] = []
        self.buttons: List[dict] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        self._current_tag = tag
        attrs_dict = {k: v for k, v in attrs}
        if tag == "a":
            self.links.append(
                {"href": attrs_dict.get("href"), "text": ""}
            )
        elif tag == "button":
            self.buttons.append({"text": ""})

    def handle_endtag(self, tag: str) -> None:
        if self._current_tag == tag:
            self._current_tag = None

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text or self._current_tag is None:
            return

        if self._current_tag == "title":
            self.title = (self.title or "") + " " + text
        elif self._current_tag in ("h1", "h2", "h3"):
            self.headings.append({"tag": self._current_tag, "text": text})
        elif self._current_tag == "a" and self.links:
            self.links[-1]["text"] = (self.links[-1]["text"] + " " + text).strip()
        elif self._current_tag == "button" and self.buttons:
            self.buttons[-1]["text"] = (self.buttons[-1]["text"] + " " + text).strip()


def analyze_site(index_path: Path) -> Dict[str, Any]:
    """
    Very lightweight 'visual' analysis:
    - Parses title, headings, links, and buttons from index.html.
    - No screenshots, no external dependencies.

    Returns:
      {
        "dom_info": { ... },
        "screenshot_path": None
      }
    """
    if not index_path.exists():
        raise FileNotFoundError(f"index.html not found at: {index_path}")

    html = index_path.read_text(encoding="utf-8", errors="ignore")

    parser = _SimpleHTMLAnalyzer()
    parser.feed(html)

    dom_info = {
        "title": parser.title.strip() if parser.title else None,
        "headings": parser.headings,
        "links": parser.links,
        "buttons": parser.buttons,
    }

    return {
        "dom_info": dom_info,
        "screenshot_path": None,
    }

