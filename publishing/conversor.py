"""Command-line entry point for the book publishing workflow."""
from __future__ import annotations

import argparse
from . import pdf, epub, site


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Aerodynamics books")
    parser.add_argument("format", choices=("pdf", "epub", "site", "all"))
    parser.add_argument("--force", action="store_true", help="Force PDF or EPUB compilation")
    parser.add_argument("--keep-aux", action="store_true", help="Keep compilation auxiliary files")
    args = parser.parse_args(argv)

    build_args = (["--force"] if args.force else []) + (["--keep-aux"] if args.keep_aux else [])
    if args.format == "pdf":
        return pdf.main(build_args)
    if args.format == "epub":
        return epub.main(build_args)
    if args.format == "site":
        return site.main()
    print("The 'all' command is not yet available: the site converter is pending.")
    return 2