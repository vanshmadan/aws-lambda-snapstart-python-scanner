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
from dataclasses import dataclass, asdict
from typing import List, Dict

@dataclass
class Finding:
    rule_id: str
    level: str
    message: str
    filename: str
    lineno: int
    col: int
    code: str = ""
    def to_dict(self) -> Dict:
        return asdict(self)

def exit_code_from_findings(findings: List[Finding], exit_on: str) -> int:
    if exit_on == "NEVER":
        return 0
    if exit_on == "ERROR":
        return 2 if any(f.level.upper() == "ERROR" for f in findings) else 0
    if exit_on == "WARN":
        return 1 if findings else 0
    return 0
