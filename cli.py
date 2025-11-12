# Copyright 2025 Vansh Madan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!/usr/bin/env python3
import argparse
import json, sys
import pathlib
from pathlib import Path
from rich.console import Console
from rich.text import Text
from snapstart_py_scanner.scanner import gather_python_files, scan_paths
from snapstart_py_scanner.findings import exit_code_from_findings
from snapstart_py_scanner.config import load_config
from snapstart_py_scanner.report import render_html_report

def comma_list(value: str | None) -> list[str]:
    """Split comma-separated CLI values into a clean list."""
    if not value:
        return []
    return [s.strip() for s in value.split(",") if s.strip()]

def load_source_lines(filepath):
    """Safely read file and return its lines."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.readlines()
    except Exception:
        return []

def format_context(lines, lineno, context=2):
    """Format code snippet with N lines before/after."""
    start = max(0, lineno - 1 - context)
    end = min(len(lines), lineno + context)
    snippet = []
    for i in range(start, end):
        prefix = "→ " if i == lineno - 1 else "  "
        snippet.append(f"{prefix}{i+1:4d} | {lines[i].rstrip()}")
    return "\n".join(snippet)

def main():
    ap = argparse.ArgumentParser(description="SnapStart Bug Scanner for Python (libcst-based)")
    ap.add_argument("path", nargs="?", default=".", help="Path to project (repo) root")
    ap.add_argument("--repo", help="Explicit repo root path (alias of positional PATH)")
    ap.add_argument("--include", help="Comma-separated glob patterns to include (e.g., 'src/**/*.py,lambda/**/*.py')")
    ap.add_argument("--exclude", help="Comma-separated glob patterns to exclude (in addition to config ignores)")
    ap.add_argument("--format", choices=["json","text","html"], help="Output format override")  # <-- add html
    ap.add_argument("--out", help="Output path for HTML/JSON report (default: ./snapstart_report.html or stdout for text)")
    ap.add_argument("--context", type=int, default=2, help="Number of context lines in HTML report (default=2)")
    args = ap.parse_args()

    repo_root = pathlib.Path(args.repo or args.path).resolve()
    cfg = load_config(repo_root)
    if args.format:
        cfg.output_format = args.format

    includes = comma_list(args.include)
    excludes = comma_list(args.exclude)

    pyfiles = gather_python_files(repo_root, includes=includes, excludes=excludes)
    findings = scan_paths(repo_root, pyfiles, extra_excludes=excludes)

    # --- HTML output path planning ---
    if cfg.output_format == "html":
        out = pathlib.Path(args.out or "snapstart_report.html").resolve()
        template_dir = pathlib.Path(__file__).parent.parent / "templates"
        # fallback: templates next to cli.py if project layout differs
        if not template_dir.exists():
            template_dir = pathlib.Path("templates").resolve()
        render_html_report(findings, repo_root, out, template_dir, context_lines=args.context)
        print(f"HTML report written to: {out}")
        sys.exit(exit_code_from_findings(findings, cfg.exit_on))

    # JSON (unchanged)
    if cfg.output_format == "json":
        if args.out:
            pathlib.Path(args.out).write_text(json.dumps([f.to_dict() for f in findings], indent=2), encoding="utf-8")
            print(f"JSON report written to: {pathlib.Path(args.out).resolve()}")
        else:
            print(json.dumps([f.to_dict() for f in findings], indent=2))
        sys.exit(exit_code_from_findings(findings, cfg.exit_on))

    # TEXT (unchanged printing with snippet if present)
    if not findings:
        print("No findings.")
    for f in findings:
        code_line = getattr(f, "code", "") or ""
        print(f"{f.level} {f.rule_id} {f.filename}:{f.lineno}:{f.col}")
        if code_line:
            print(f"→ {code_line}")
        print(f"   {f.message}\n")

    sys.exit(exit_code_from_findings(findings, cfg.exit_on))

if __name__ == "__main__":
    main()
