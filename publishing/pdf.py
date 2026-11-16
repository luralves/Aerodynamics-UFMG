"""Build or collect PDFs for the Aerodynamics book collection.

Run from the repository root with: python -m publishing pdf
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
OUTPUT_DIR = ROOT / "build" / "pdf"
AUX_EXTENSIONS = {
    ".aux", ".bbl", ".bcf", ".blg", ".fdb_latexmk", ".fls",
    ".log", ".out", ".run.xml", ".synctex.gz", ".toc", ".lof",
    ".lot", ".nav", ".snm", ".xdv", ".acn", ".acr", ".alg",
    ".glg", ".glo", ".gls", ".ist", ".idx", ".ilg", ".ind",
}


def extract_title(source: str) -> str:
    """Extract a simple LaTeX title with balanced braces (no macro expansion)."""
    source = re.sub(r"(?<!\\)%[^\n]*", "", source)
    match = re.search(r"\\title\s*(?:\[[^]]*\]\s*)?\{", source)
    if not match:
        raise ValueError("Missing \\title{...} in main.tex")
    start = match.end()
    depth = 1
    pos = start
    while pos < len(source):
        char = source[pos]
        if char == "{" and (pos == 0 or source[pos - 1] != "\\"):
            depth += 1
        elif char == "}" and (pos == 0 or source[pos - 1] != "\\"):
            depth -= 1
            if depth == 0:
                title = source[start:pos].strip()
                title = re.sub(r"\s+", " ", title)
                if not title or "\\" in title:
                    raise ValueError("Title must be plain text in \\title{...}")
                return title
        pos += 1
    raise ValueError("Unbalanced braces in \\title{...}")


def safe_filename(title: str) -> str:
    title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", title).strip(" .")
    if not title or title in {".", ".."}:
        raise ValueError("Invalid title for PDF filename")
    return title + ".pdf"


def clean_auxiliary_files(folder: Path) -> int:
    """Remove known main.* artifacts and chapter .aux files in content/."""
    count = 0

    # Only remove recognized LaTeX-generated files from the main.tex folder.
    for path in folder.glob("main.*"):
        if not path.is_file() or path.name in {"main.tex", "main.pdf"}:
            continue
        if any(path.name.endswith(suffix) for suffix in AUX_EXTENSIONS):
            path.unlink()
            count += 1

    # \include{content/chapter} creates content/chapter.aux. This also covers
    # nested content/ directories, without touching .tex, figures or other files.
    content = folder / "content"
    if content.is_dir():
        for path in content.rglob("*.aux"):
            if path.is_file():
                path.unlink()
                count += 1

    return count


def process_main(main: Path, force: bool, keep_aux: bool) -> bool:
    folder = main.parent
    language = folder.name
    title = extract_title(main.read_text(encoding="utf-8"))
    destination = OUTPUT_DIR / language / safe_filename(title)
    source_pdf = folder / "main.pdf"

    if force or not source_pdf.is_file():
        if shutil.which("latexmk") is None:
            raise RuntimeError("latexmk not found; install latexmk and TeX Live")
        print(f"[BUILD] {main.relative_to(ROOT)}")
        subprocess.run(
            ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", "main.tex"],
            cwd=folder, check=True,
        )
        if not source_pdf.is_file():
            raise RuntimeError(f"PDF was not created: {source_pdf}")
    else:
        print(f"[REUSE] {main.relative_to(ROOT)}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_pdf, destination)
    print(f"[COPY]  {destination.relative_to(ROOT)}")
    if not keep_aux:
        count = clean_auxiliary_files(folder)
        print(f"[CLEAN] {count} auxiliary files (main.* and content/**/*.aux)")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect or compile PDFs for all books")
    parser.add_argument("--force", action="store_true", help="Recompile even if main.pdf exists")
    parser.add_argument("--keep-aux", action="store_true", help="Preserve LaTeX auxiliary files")
    args = parser.parse_args(argv)

    if not BOOK_DIR.is_dir():
        print(f"Book directory not found: {BOOK_DIR}", file=sys.stderr)
        return 2
    mains = sorted(BOOK_DIR.rglob("main.tex"))
    if not mains:
        print("No main.tex found in book/")
        return 0
    failures = 0
    for source in mains:
        try:
            process_main(source, args.force, args.keep_aux)
        except (OSError, ValueError, subprocess.CalledProcessError, RuntimeError) as error:
            failures += 1
            print(f"[ERROR] {source}: {error}", file=sys.stderr)
    print(f"Finished: {len(mains) - failures}/{len(mains)} books processed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
