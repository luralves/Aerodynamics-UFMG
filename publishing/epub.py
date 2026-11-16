"""Build or collect EPUB 3 files for the Aerodynamics book collection.

Usage (from the repository root):
    python3 -m publishing epub
    python3 -m publishing epub --force
    python3 -m publishing epub --keep-aux

Requires TeX4ebook and Biber; some image conversions also need dvisvgm. Conversion uses an isolated
build directory so that PDF/VS Code auxiliary files are not affected.
"""
from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from .pdf import BOOK_DIR, ROOT, extract_title, safe_filename

OUTPUT_DIR = ROOT / "build" / "epub"
LOG_DIR = ROOT / "build" / ".epub-logs"
WORK_DIR = ROOT / "build" / ".epub-work"


def epub_filename(title: str) -> str:
    """Use the same filename sanitization rules as the PDF converter."""
    return safe_filename(title)[:-4] + ".epub"


def _check_dependencies() -> None:
    for executable, package in (
        ("tex4ebook", "TeX4ebook (TeX Live)"),
        ("biber", "Biber (bibliography)"),
    ):
        if shutil.which(executable) is None:
            raise RuntimeError(f"{executable} not found; install {package}")


def _run(command: list[str], cwd: Path, log: Path) -> None:
    """Run one build stage and preserve its full output in the build log."""
    with log.open("a", encoding="utf-8") as stream:
        stream.write("\n$ " + " ".join(command) + "\n")
        stream.flush()
        result = subprocess.run(
            command, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT,
            check=False,
        )
    if result.returncode != 0:
        raise RuntimeError(
            f"{command[0]} failed (exit code {result.returncode})"
        )


def _validate_epub(path: Path) -> None:
    """Reject missing/invalid EPUB archives rather than copying a bad result."""
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"EPUB was not created: {path}")
    try:
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None or "mimetype" not in archive.namelist():
                raise RuntimeError(f"Invalid EPUB archive: {path}")
            if archive.read("mimetype").strip() != b"application/epub+zip":
                raise RuntimeError(f"Invalid EPUB mimetype: {path}")
    except zipfile.BadZipFile as exc:
        raise RuntimeError(f"Invalid EPUB archive: {path}") from exc


CHAPTER_TOC_PLACEHOLDER = re.compile(
    r"""<div\b[^>]*\bclass\s*=\s*['"]aero-chapter-toc-placeholder['"][^>]*>\s*</div>""",
    re.IGNORECASE,
)
HEADING_RE = re.compile(
    r'<h(?P<level>[1-6])\b(?P<attrs>[^>]*)>(?P<body>.*?)</h[1-6]>',
    re.IGNORECASE | re.DOTALL,
)
CLASS_RE = re.compile(r"\bclass\s*=\s*(['\"])(.*?)\1", re.IGNORECASE | re.DOTALL)
ID_RE = re.compile(r"\bid\s*=\s*(['\"])(.*?)\1", re.IGNORECASE | re.DOTALL)
TITLEMARK_RE = re.compile(
    r'<span\b[^>]*\bclass\s*=\s*["\'][^"\']*\btitlemark\b[^"\']*["\'][^>]*>(.*?)</span>',
    re.IGNORECASE | re.DOTALL,
)
TAG_RE = re.compile(r"<[^>]+>", re.DOTALL)


def _plain_text(source: str) -> str:
    # TeX4ht often puts an empty reference anchor inside the heading.
    result = TAG_RE.sub("", source).replace("\x00", "")
    return re.sub(r"\s+", " ", html.unescape(result)).strip()


def _section_links(xhtml: str) -> list[tuple[str, str, str]]:
    """Collect numbered sections of this chapter (not bibliography headings)."""
    sections: list[tuple[str, str, str]] = []
    for heading in HEADING_RE.finditer(xhtml):
        klass = CLASS_RE.search(heading.group("attrs"))
        if not klass or "sectionHead" not in klass.group(2).split():
            continue
        anchor = ID_RE.search(heading.group("attrs"))
        number = TITLEMARK_RE.search(heading.group("body"))
        if not anchor or not number:
            continue
        title = _plain_text(TITLEMARK_RE.sub("", heading.group("body"), count=1))
        label = _plain_text(number.group(1))
        if title:
            sections.append((anchor.group(2), label, title))
    return sections


def _chapter_nav(sections: list[tuple[str, str, str]], language: str) -> str:
    caption = "Neste capítulo" if language.lower() == "pt-br" else "In this chapter"
    entries = "\n".join(
        '  <li><a href="#{anchor}"><span class="aero-local-toc-number">{number}</span> {title}</a></li>'.format(
            anchor=html.escape(anchor, quote=True),
            number=html.escape(number),
            title=html.escape(title),
        )
        for anchor, number, title in sections
    )
    return (
        f'<nav class="aero-local-toc" aria-label="{html.escape(caption, quote=True)}">\n'
        f'  <div class="aero-local-toc-title">{html.escape(caption)}</div>\n'
        f'  <ol>\n{entries}\n  </ol>\n</nav>'
    )


def _enhance_epub(path: Path, language: str) -> int:
    """Create per-chapter linked TOCs without changing the LaTeX/PDF files.

    An EPUB is a ZIP container. We rewrite the chapter XHTML entries, keeping
    the EPUB's mimetype entry first and uncompressed as required by EPUB.
    """
    updated = 0
    replacements: dict[str, bytes] = {}
    with zipfile.ZipFile(path, "r") as archive:
        entries = archive.infolist()
        for info in entries:
            if not info.filename.lower().endswith((".xhtml", ".html")):
                continue
            source = archive.read(info.filename).decode("utf-8")
            if not CHAPTER_TOC_PLACEHOLDER.search(source):
                continue
            sections = _section_links(source)
            enhanced = CHAPTER_TOC_PLACEHOLDER.sub(
                lambda _: _chapter_nav(sections, language) if sections else "", source
            )
            replacements[info.filename] = enhanced.encode("utf-8")
            if sections:
                updated += 1
        if not replacements:
            return 0
        # Copy the original entries and metadata. EPUB 3 requires the first
        # entry to be 'mimetype', stored without compression.
        temp_path = path.with_suffix(".rewritten.epub")
        try:
            with zipfile.ZipFile(temp_path, "w") as result:
                for info in sorted(entries, key=lambda item: item.filename != "mimetype"):
                    content = replacements.get(info.filename)
                    if content is None:
                        content = archive.read(info.filename)
                    if info.filename == "mimetype":
                        info.compress_type = zipfile.ZIP_STORED
                    result.writestr(info, content)
            os.replace(temp_path, path)
        finally:
            temp_path.unlink(missing_ok=True)
    return updated


def _copy_sources(main: Path, workspace: Path) -> Path:
    """Create an isolated copy with the same paths relative to book/.

    Older TeX4ebook versions don't accept ``-B``. Running it from the
    original folder would create auxiliary files next to main.tex and
    content/*.tex, so all compilation happens in this temporary tree.
    """
    relative = main.parent.relative_to(BOOK_DIR)
    if len(relative.parts) < 2:
        raise ValueError(f"Unexpected main.tex location: {main}")

    staged_book = workspace / "book"
    staged_book.mkdir()

    # Shared class and bibliography, usually book/aerodynamics.cls and
    # book/reference.bib. Keep other files here, as they can be resources.
    for entry in BOOK_DIR.iterdir():
        if entry.is_file():
            shutil.copy2(entry, staged_book / entry.name)

    # Copy the containing volume: its languages may share a figures/ folder.
    # Preserve PDF figures, but do not copy generated main.pdf/main.epub files.
    def ignore_artifacts(_folder: str, names: list[str]) -> set[str]:
        excluded = {"__pycache__", ".git", "main.pdf", "main.epub"}
        auxiliary_suffixes = (
            ".aux", ".bcf", ".bbl", ".blg", ".log", ".toc", ".out",
            ".fls", ".fdb_latexmk", ".synctex.gz", ".run.xml",
            ".4ct", ".4tc", ".dvi", ".idv", ".lg", ".xref",
        )
        return {name for name in names if name in excluded or
                name.endswith(auxiliary_suffixes)}

    volume = relative.parts[0]
    shutil.copytree(
        BOOK_DIR / volume,
        staged_book / volume,
        ignore=ignore_artifacts,
    )
    staged_main = staged_book / relative / main.name
    if not staged_main.is_file():
        raise RuntimeError(f"Staged LaTeX file missing: {staged_main}")
    return staged_main


def _compile(main: Path, workspace: Path, log: Path) -> Path:
    """Convert using TeX4ebook options supported by older TeX Live versions."""
    staged_main = _copy_sources(main, workspace)
    working_dir = staged_main.parent
    output_dir = workspace / "output"
    output_dir.mkdir()

    # Do NOT pass -B: older versions of tex4ebook report
    # 'unrecognized parameter: B'. Isolation is provided by _copy_sources.
    config_file = Path(__file__).with_name("epub.cfg")
    if not config_file.is_file():
        raise RuntimeError(f"Missing TeX4ebook configuration: {config_file}")
    command = [
        "tex4ebook", "-f", "epub3", "-c", str(config_file),
        "-d", str(output_dir), "main.tex",
    ]

    print(f"[BUILD] {main.relative_to(ROOT)}")
    _run(command, working_dir, log)

    # The .bcf is in the staged working directory, because build-dir (-B)
    # is not used. Run Biber here to resolve biblatex references.
    if (working_dir / "main.bcf").is_file():
        _run(["biber", "main"], working_dir, log)
        _run(command, working_dir, log)

    generated = output_dir / "main.epub"
    _validate_epub(generated)
    toc_count = _enhance_epub(generated, main.parent.name)
    _validate_epub(generated)
    print(f"[TOC]   {toc_count} chapter tables of contents added")
    return generated


def process_main(main: Path, force: bool, keep_aux: bool) -> bool:
    source_dir = main.parent
    language = source_dir.name
    title = extract_title(main.read_text(encoding="utf-8"))
    name = epub_filename(title)
    source_epub = source_dir / "main.epub"
    destination = OUTPUT_DIR / language / name

    if not force and source_epub.is_file():
        _validate_epub(source_epub)
        print(f"[REUSE] {main.relative_to(ROOT)}")
    else:
        _check_dependencies()
        if keep_aux:
            WORK_DIR.mkdir(parents=True, exist_ok=True)
        workspace = Path(tempfile.mkdtemp(
            prefix=f"aero-epub-{language}-",
            dir=WORK_DIR if keep_aux else None,
        ))
        log = workspace / "conversion.log"
        try:
            try:
                generated = _compile(main, workspace, log)
                # Keep main.epub beside main.tex, just as main.pdf is kept.
                # The original is not touched if conversion fails.
                shutil.copy2(generated, source_epub)
            except (OSError, RuntimeError) as exc:
                if log.is_file():
                    saved_log = LOG_DIR / language / (name + ".log")
                    saved_log.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(log, saved_log)
                    raise RuntimeError(
                        f"{exc}; details: {saved_log.relative_to(ROOT)}"
                    ) from exc
                raise
        finally:
            if keep_aux:
                print(f"[KEEP]  {workspace} (TeX4ebook auxiliaries)")
            else:
                shutil.rmtree(workspace, ignore_errors=True)

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_epub, destination)
    print(f"[COPY]  {destination.relative_to(ROOT)}")
    if not keep_aux:
        print("[CLEAN] Temporary EPUB build files removed")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect or compile EPUB 3 books")
    parser.add_argument(
        "--force", action="store_true",
        help="Recompile even if main.epub already exists",
    )
    parser.add_argument(
        "--keep-aux", action="store_true",
        help="Keep intermediate files in build/.epub-work/",
    )
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
        except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as error:
            failures += 1
            print(f"[ERROR] {source}: {error}", file=sys.stderr)
    print(f"Finished: {len(mains) - failures}/{len(mains)} books processed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
