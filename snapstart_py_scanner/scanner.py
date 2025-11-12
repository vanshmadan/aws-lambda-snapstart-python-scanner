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
from ast import mod
import pathlib, fnmatch
from typing import List
import libcst as cst
from .config import load_config, RuleConfig
from .findings import Finding
from .rules import ModuleLevelVisitor

def _match_any(path: pathlib.Path, globs: List[str]) -> bool:
    if not globs:
        return True
    s = str(path).replace("\\","/")
    return any(fnmatch.fnmatch(s, g) for g in globs)

def gather_python_files(root: pathlib.Path, includes: List[str] | None = None, excludes: List[str] | None = None) -> List[pathlib.Path]:
    files: List[pathlib.Path] = []
    for p in root.rglob("*.py"):
        if not p.is_file():
            continue
        s = str(p).replace("\\","/")
        if includes and not any(fnmatch.fnmatch(s, pat) for pat in includes):
            continue
        if excludes and any(fnmatch.fnmatch(s, pat) for pat in excludes):
            continue
        files.append(p)
    return files

def scan_paths(root: pathlib.Path, paths: List[pathlib.Path], extra_excludes: List[str] | None = None) -> List[Finding]:
    cfg: RuleConfig = load_config(root)
    findings: List[Finding] = []
    for p in paths:
        if cfg.path_ignored(p, extra_excludes):
            continue
        try:
            code = p.read_text(encoding="utf-8")
        except Exception as e:
            print(f"[WARN] Could not read {p}: {e}")
            continue

        try:
            mod = cst.parse_module(code)
        except Exception as e:
            print(f"[WARN] Skipping {p}: {e}")
            continue

      # after parsing and wrapping
        wrapper = cst.metadata.MetadataWrapper(mod)
        visitor = ModuleLevelVisitor(str(p), cfg.severity, cfg.hook_names, source_text=code)  # <-- pass code
        wrapper.visit(visitor)

        print(f"Scanning {p}")
    
        for f in visitor.findings:
            findings.append(Finding(
                rule_id=f["rule_id"],
                level=f["level"],
                message=f["message"],
                filename=str(p),
                lineno=f["lineno"],
                col=f["col"],
                code=f.get("code", "")
            ))
    return findings
