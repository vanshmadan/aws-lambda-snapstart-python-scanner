# SnapStart Bug Scanner 
This is a lightweight static analyzer to spot AWS Lambda **SnapStart** anti-patterns in Python code, inspired by the Java SnapStart Bug Scanner. It focuses on code executed that can behave badly across snapshot/restore.

## Rules Implemented (8)
- **PY001_MUTABLE_MODULE_STATE (WARN):** Mutable objects (list/dict/set) created at module level.
- **PY002_NON_IDEMPOTENT_INIT (ERROR):** Side‑effect calls at import time: `requests.*`, `subprocess.*`, `os.system`, etc.
- **PY003_BACKGROUND_THREADS (ERROR):** `threading.Thread/Timer`, `ThreadPoolExecutor`, schedulers created at import time.
- **PY004_OPEN_SOCKETS_FILES (ERROR):** `socket.socket()`, `open()` at import time.
- **PY005_RANDOM_TIME_UUID_AT_INIT (WARN):** `random.*`, `uuid.uuid*`, `time.time()`, `datetime.now()` computed at import time.
- **PY006_BOTO3_CLIENT_AT_INIT (ERROR):** `boto3.client/resource` created at module level.
- **PY007_TMP_FILES_CREDS_AT_INIT (WARN):** writing to `/tmp` or using `tempfile.*` at import time.
- **PY008_MISSING_RUNTIME_HOOKS (WARN):** If any hazardous patterns (PY002/3/4/6/7) exist but no runtime hook functions (`before_snapshot` / `after_restore` etc.) are found.

Inline ignores:
```py
requests.get("https://example.com")  # snapstart: ignore[PY002]
```

## Install
```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

## Run against a repo path
```bash

git clone git@github.com:vanshmadan/aws-lambda-snapstart-python-scanner.git

cd aws-lambda-snapstart-python-scanner

# scan current folder
python cli.py . --format text

# scan an explicit repo path
python cli.py --repo /path/to/repo --format json

# only scan code under src/ and lambda/ folders
python cli.py /path/to/repo --include "src/**/*.py,lambda/**/*.py"

# exclude tests and migration scripts in addition to default ignores
python cli.py /path/to/repo --exclude "**/tests/**,**/migrations/**" --format text
```

### Exit codes
- Controlled via `.snapstartpy.yaml` `exit_on`: `ERROR` (default), `WARN`, or `NEVER`.

- `ERROR`: exit 2 if any ERROR findings

- `WARN`: exit 1 if any findings

- `NEVER`: always 0

## Config file: `.snapstartpy.yaml`
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

## Limitations

Static analysis is heuristic. Validate critical behavior with real SnapStart runs and runtime hooks.
