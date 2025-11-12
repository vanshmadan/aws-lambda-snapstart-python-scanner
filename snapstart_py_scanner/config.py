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
from dataclasses import dataclass, field
from typing import Dict, List
import yaml
import fnmatch
import pathlib

DEFAULT_CONFIG = {
    "severity": {
        "PY001_MUTABLE_MODULE_STATE": "WARN",
        "PY002_NON_IDEMPOTENT_INIT": "ERROR",
        "PY003_BACKGROUND_THREADS": "ERROR",
        "PY004_OPEN_SOCKETS_FILES": "ERROR",
        "PY005_RANDOM_TIME_UUID_AT_INIT": "WARN",
        "PY006_BOTO3_CLIENT_AT_INIT": "ERROR",
        "PY007_TMP_FILES_CREDS_AT_INIT": "WARN",
        "PY008_MISSING_RUNTIME_HOOKS": "WARN"
    },
    "ignore_paths": [
        "**/.venv/**", "**/venv/**", "**/.git/**", "**/node_modules/**",
        "**/dist/**", "**/build/**", "**/.eggs/**", "**/.mypy_cache/**",
        "**/__pycache__/**"
    ],
    "hook_names": [
        "before_snapshot", "after_restore",
        "snapstart_before_snapshot", "snapstart_after_restore"
    ],
    "exit_on": "ERROR",
    "format": "json"
}

@dataclass
class RuleConfig:
    severity: Dict[str, str] = field(default_factory=lambda: DEFAULT_CONFIG["severity"])
    ignore_paths: List[str] = field(default_factory=lambda: list(DEFAULT_CONFIG["ignore_paths"]))
    hook_names: List[str] = field(default_factory=lambda: DEFAULT_CONFIG["hook_names"])
    exit_on: str = "ERROR"
    output_format: str = "json"

    def sev(self, rule_id: str) -> str:
        return self.severity.get(rule_id, "WARN")

    def path_ignored(self, path: pathlib.Path, extra_excludes: List[str] | None = None) -> bool:
        s = str(path).replace("\\","/")
        for pat in self.ignore_paths:
            if fnmatch.fnmatch(s, pat):
                return True
        for pat in (extra_excludes or []):
            if fnmatch.fnmatch(s, pat):
                return True
        return False

def load_config(root: pathlib.Path) -> RuleConfig:
    cfg_path = root / ".snapstartpy.yaml"
    if not cfg_path.exists():
        return RuleConfig()
    data = yaml.safe_load(cfg_path.read_text()) or {}
    merged = DEFAULT_CONFIG.copy()
    # merge top-level fields
    for k in ["ignore_paths","hook_names","exit_on","format"]:
        if k in data and data[k] is not None:
            merged[k] = data[k]
    # merge severity dict
    sev = merged["severity"].copy()
    sev.update((data.get("severity") or {}))
    merged["severity"] = sev
    return RuleConfig(
        severity=merged["severity"],
        ignore_paths=list(merged["ignore_paths"]),
        hook_names=list(merged["hook_names"]),
        exit_on=str(merged["exit_on"]).upper(),
        output_format=str(merged["format"]).lower()
    )
