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
import libcst as cst
import libcst.matchers as m
from typing import List, Dict, Set

PY001 = "PY001_MUTABLE_MODULE_STATE"
PY002 = "PY002_NON_IDEMPOTENT_INIT"
PY003 = "PY003_BACKGROUND_THREADS"
PY004 = "PY004_OPEN_SOCKETS_FILES"
PY005 = "PY005_RANDOM_TIME_UUID_AT_INIT"
PY006 = "PY006_BOTO3_CLIENT_AT_INIT"
PY007 = "PY007_TMP_FILES_CREDS_AT_INIT"
PY008 = "PY008_MISSING_RUNTIME_HOOKS"

IGNORE_TOKEN = "snapstart: ignore"
MUTABLE_LITERALS = (cst.List, cst.Dict, cst.Set)

SIDE_EFFECT_FUNCS = [
    ("requests", {"get","post","put","patch","delete","head","request"}),
    ("subprocess", {"run","Popen","call","check_call","check_output"}),
    ("os", {"system"}),
]

THREAD_NAMES = [
    ("threading", {"Thread","Timer"}),
    ("concurrent.futures", {"ThreadPoolExecutor","ProcessPoolExecutor"}),
    ("apscheduler.schedulers.background", {"BackgroundScheduler"}),
    ("sched", {"scheduler"}),
]

def dotted_name(node: cst.BaseExpression) -> str:
    names = []
    cur = node
    while isinstance(cur, cst.Attribute):
        if isinstance(cur.attr, cst.Name):
            names.append(cur.attr.value)
        cur = cur.value
    if isinstance(cur, cst.Name):
        names.append(cur.value)
    names.reverse()
    return ".".join(names)

def has_inline_ignore(comment_list, rule_id: str) -> bool:
    for c in comment_list or []:
        # If it's an EmptyLine or Comment, extract the string safely
        comment_value = None
        if hasattr(c, "value"):  # for Comment objects
            comment_value = c.value
        elif hasattr(c, "comment") and c.comment:  # for EmptyLine with a comment
            comment_value = c.comment.value
        if not comment_value:
            continue

        txt = comment_value.lstrip("# ").strip()
        if txt.startswith("snapstart: ignore"):
            if "[" in txt and "]" in txt:
                inside = txt.split("[", 1)[1].split("]", 1)[0]
                ids = [s.strip() for s in inside.split(",") if s.strip()]
                return rule_id in ids
            return True
    return False

class ModuleLevelVisitor(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (cst.metadata.PositionProvider,)

    def __init__(self, filename: str, severities: Dict[str,str], hook_names: List[str], source_text: str):
        self.filename = filename
        self.sev = severities
        self.hook_names = set(hook_names)
        self.findings = []
        self.seen_hooks: Set[str] = set()
        self._module_level_nodes: List[cst.CSTNode] = []
        self._source_lines = source_text.splitlines()  # 0-indexed backing text

    def visit_Module(self, node: cst.Module) -> None:
        self._module_level_nodes = list(node.body)

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        fn = node.name.value
        if fn in self.hook_names:
            self.seen_hooks.add(fn)

    def leave_Module(self, node: cst.Module) -> None:
        for stmt in self._module_level_nodes:
            comments = []
            if hasattr(stmt, "leading_lines"):
                comments = [ll.comment for ll in getattr(stmt, "leading_lines")]
            trailing_comment = getattr(stmt, "trailing_whitespace", None)
            if trailing_comment and trailing_comment.comment:
                comments.append(trailing_comment.comment)

            if isinstance(stmt, cst.SimpleStatementLine):
                for small in stmt.body:
                    # PY001 mutable literals at module import
                    if isinstance(small, cst.Assign):
                        value = small.value
                        if isinstance(value, MUTABLE_LITERALS) or m.matches(value, m.Call(func=m.Name("set"))) or m.matches(value, m.Call(func=m.Name("list"))) or m.matches(value, m.Call(func=m.Name("dict"))):
                            if not has_inline_ignore(comments, PY001):
                                self._emit(PY001, "Mutable object created at module level; consider making immutable or moving to handler.", stmt)

                    # Calls at module import
                    if isinstance(small, cst.Expr) and isinstance(small.value, cst.Call):
                        call = small.value
                        dname = dotted_name(call.func)
                        mod = dname.split(".")[0] if dname else ""
                        func = dname.split(".")[-1] if dname else ""

                        # PY002 non-idempotent side effects
                        for mname, funcs in SIDE_EFFECT_FUNCS:
                            if (mod == mname and func in funcs):
                                if not has_inline_ignore(comments, PY002):
                                    self._emit(PY002, f"Potential non-idempotent side-effect call '{dname}' at module import.", stmt)

                        # PY006 boto3
                        if dname in ("boto3.client","boto3.resource"):
                            if not has_inline_ignore(comments, PY006):
                                self._emit(PY006, "boto3 client/resource created at module level; recreate per invocation or in restore hook.", stmt)

                        # PY004 sockets/files
                        if dname in ("socket.socket",):
                            if not has_inline_ignore(comments, PY004):
                                self._emit(PY004, "Socket opened at module level; reopen per invocation or in restore hook.", stmt)
                        if dname in ("open","pathlib.Path.open"):
                            if not has_inline_ignore(comments, PY004):
                                self._emit(PY004, "File opened at module level; use context manager in handler or reopen in restore hook.", stmt)

                        # PY005 randomness/time/uuid
                        if dname in ("random.seed","random.random","uuid.uuid4","uuid.uuid1","time.time","datetime.datetime.now","datetime.datetime.utcnow"):
                            if not has_inline_ignore(comments, PY005):
                                self._emit(PY005, f"Non-deterministic value computed at module import via '{dname}'.", stmt)

                        # PY007 tmp (tempfile.* or open('/tmp/...'))
                        if dname == "open" and call.args and isinstance(call.args[0].value, cst.SimpleString):
                            s = call.args[0].value.evaluated_value
                            if isinstance(s, str) and s.startswith("/tmp/"):
                                if not has_inline_ignore(comments, PY007):
                                    self._emit(PY007, "Writing/reading in /tmp at module import; defer to handler or restore hook.", stmt)
                        if dname.startswith("tempfile."):
                            if not has_inline_ignore(comments, PY007):
                                self._emit(PY007, "Temporary file created at module import; may not survive snapshot/restore.", stmt)

                    # PY003 background threads/executors created at import (assignment)
                    if isinstance(small, cst.Assign) and isinstance(small.value, cst.Call):
                        dname = dotted_name(small.value.func)
                        if any(dname.endswith("." + n) for _, names in THREAD_NAMES for n in names):
                            if not has_inline_ignore(comments, PY003):
                                self._emit(PY003, f"Background thread/executor '{dname}' created at module level.", stmt)

            # Also catch foo = Thread(...); foo.start() as a direct call
            if isinstance(stmt, cst.SimpleStatementLine):
                for small in stmt.body:
                    if isinstance(small, cst.Expr) and isinstance(small.value, cst.Call):
                        call = small.value
                        if isinstance(call.func, cst.Attribute) and call.func.attr.value == "start":
                            recv = call.func.value
                            if isinstance(recv, cst.Call):
                                dname = dotted_name(recv.func)
                                if dname.endswith("threading.Thread") or dname.endswith("Thread"):
                                    if not has_inline_ignore(getattr(stmt, "leading_lines", []), PY003):
                                        self._emit(PY003, "Thread started at module level.", stmt)

        hazardous = any(f["rule_id"] in {PY002, PY003, PY004, PY006, PY007} for f in self.findings)
        if hazardous and not self.seen_hooks:
            self._emit(PY008, "Hazardous init detected but no runtime restore hooks found. Define restore hooks (e.g., after_restore).", node)
 

    def _emit(self, rule_id: str, message: str, node: cst.CSTNode) -> None:
        try:
            meta = self.get_metadata(cst.metadata.PositionProvider, node, None)
            lineno = meta.start.line if meta else 1
            col = meta.start.column if meta else 0
        except Exception:
            lineno, col = 1, 0

        # Slice the offending source line safely
        code_snippet = ""
        try:
            # libcst lines are 1-indexed; our list is 0-indexed
            line = self._source_lines[lineno - 1] if 1 <= lineno <= len(self._source_lines) else ""
            code_snippet = line.strip()
            if len(code_snippet) > 160:
                code_snippet = code_snippet[:157] + "..."
        except Exception:
            code_snippet = ""

        self.findings.append({
            "rule_id": rule_id,
            "level": self.sev.get(rule_id, "WARN"),
            "message": message,
            "lineno": lineno,
            "col": col,
            "filename": self.filename,
            "code": code_snippet,
        })
