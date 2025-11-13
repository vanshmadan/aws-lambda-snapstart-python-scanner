# SnapStart Bug Scanner 
This is a lightweight static analyzer to spot AWS Lambda **SnapStart** anti-patterns in Python code, inspired by the Java SnapStart Bug Scanner. It focuses on code executed that can behave badly across snapshot/restore.

---

## 🚀 Features
- 🔍 Scans your **entire repository** recursively for Python files.  
- 🧠 Detects 8 key SnapStart-incompatible categories (mutable globals, non-idempotent init, random init, etc.).  
- ⚙️ Configurable via `.snapstart-scan.yaml` (includes ignore patterns, severity levels, and hook names).  
- 💬 Supports multiple output formats:
  - `text` (CLI output)
  - `json` (for CI/CD or scripting)
  - `html` (beautiful Jinja2-based report)
- 🧩 Inline suppression: use `# snapstart: ignore[PY001]` to skip specific findings.

---

## Install
```bash
git clone git@github.com:vanshmadan/aws-lambda-snapstart-python-scanner.git
cd aws-lambda-snapstart-python-scanner
python -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

## Run against a repo path
```bash
# scan current folder
python cli.py . --format text

# scan an explicit repo path
python cli.py --repo /path/to/repo --format json

# only scan code under src/ and lambda/ folders
python cli.py /path/to/repo --include "src/**/*.py,lambda/**/*.py"

# exclude tests and migration scripts in addition to default ignores
python cli.py /path/to/repo --exclude "**/tests/**,**/migrations/**" --format text
```

## Example HTML Report
Generate an interactive HTML report:
```
python cli.py --repo /path/to/repo --format html
```
This produces:
```
snapstart_report.html
```
---
 
## Rules Implemented (8)
| Rule ID                            | Description                                                          |
| ---------------------------------- | -------------------------------------------------------------------- |
| **PY001_MUTABLE_MODULE_STATE**     | Mutable global state (lists, dicts, sets) created at import time.    |
| **PY002_NON_IDEMPOTENT_INIT**      | Side-effectful I/O (requests, subprocess, os.system) at import time. |
| **PY003_BACKGROUND_THREADS**       | Thread or executor started during import.                            |
| **PY004_OPEN_SOCKETS_FILES**       | Open files/sockets before handler init.                              |
| **PY005_RANDOM_TIME_UUID_AT_INIT** | Randomness/time/UUID usage at module init.                           |
| **PY006_BOTO3_CLIENT_AT_INIT**     | Boto3 client/resource created globally.                              |
| **PY007_TMP_FILES_CREDS_AT_INIT**  | Temp files or credentials stored in `/tmp` during init.              |
| **PY008_MISSING_RUNTIME_HOOKS**    | Hazardous init without restore hooks (e.g., `after_restore`).        |



### Exit codes
- Controlled via `.snapstartpy.yaml` `exit_on`: `ERROR` (default), `WARN`, or `NEVER`.

- `ERROR`: exit 2 if any ERROR findings

- `WARN`: exit 1 if any findings

- `NEVER`: always 0

## Config file: (.snapstart-scan.yaml)
```yaml
severity:
  PY002_NON_IDEMPOTENT_INIT: ERROR
ignore_paths:
  - "tests/**"
  - "**/__pycache__/**"
hook_names:
  - before_snapshot
  - after_restore
exit_on: ERROR
format: json
```

## Feedback

```
Have suggestions or want to contribute?
Open a GitHub issue
Or DM me on LinkedIn
```
