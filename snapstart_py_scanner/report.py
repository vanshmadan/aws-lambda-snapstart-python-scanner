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

from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .findings import Finding
from collections import Counter, defaultdict
from jinja2 import Environment, FileSystemLoader

def _read_lines(path: str) -> list[str]:
    try:
        return Path(path).read_text(encoding="utf-8").splitlines()
    except Exception:
        return []


def _with_context(f: Finding, default_ctx: int = 2) -> Dict[str, Any]:
    lines = _read_lines(f.filename)
    ln = f.lineno
    start = max(1, ln - default_ctx)
    end = min(len(lines), ln + default_ctx)
    chunk = []
    for i in range(start, end + 1):
        if i - 1 < 0 or i - 1 >= len(lines):
            continue
        chunk.append({
            "n": i,
            "text": lines[i - 1].rstrip("\n"),
            "is_hit": (i == ln),
        })
    d = f.to_dict()
    d["context"] = chunk
    return d

def _group_by_rule(findings: List[Finding]) -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = {}
    for f in findings:
        out.setdefault(f.rule_id, []).append(_with_context(f))
    return out

def _group_by_file(findings: List[Finding]) -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = {}
    for f in findings:
        out.setdefault(f.filename, []).append(_with_context(f))
    return out

def severity_counts(findings: List[Finding]) -> Dict[str, int]:
    counts = {"ERROR": 0, "WARN": 0, "INFO": 0}
    for f in findings:
        lvl = (f.level or "WARN").upper()
        if lvl not in counts:
            counts[lvl] = 0
        counts[lvl] += 1
    return counts

def rule_counts(findings: List[Finding]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for f in findings:
        out[f.rule_id] = out.get(f.rule_id, 0) + 1
    return out


def render_html_report(findings, repo_root, out_path, template_dir, context_lines=3):
    env = Environment(loader=FileSystemLoader(template_dir))
    tpl = env.get_template("report.html.j2")

    # ✅ Compute severity counts
    levels = [f.level for f in findings]
    counts = Counter(levels)
    for k in ("ERROR", "WARN", "INFO"):
        counts.setdefault(k, 0)

    # ✅ Compute counts by rule
    counts_by_rule = Counter(f.rule_id for f in findings)

    # ✅ Enrich findings with code context
    findings_with_ctx = [_with_context(f, default_ctx=context_lines) for f in findings]

    # ✅ Group by severity (for clean separation in template)
    grouped_findings = defaultdict(list)
    for f in findings_with_ctx:
        grouped_findings[f["level"]].append(f)

    html = tpl.render(
        repo_root=repo_root,
        counts=counts,
        counts_by_rule=counts_by_rule,
        grouped_findings=grouped_findings,
        context_lines=context_lines,
    )

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[INFO] HTML report written to: {out_path}")
