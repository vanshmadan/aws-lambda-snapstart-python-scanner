#  AWS Lambda SnapStart Bug Scanner (Python)

**AWS Lambda SnapStart Python Scanner** is a static analysis tool that detects **SnapStart-incompatible initialization patterns** in AWS Lambda Python functions.

It is inspired by the official SnapStart Bug Scanner for Java — but implemented in Python using [`libcst`](https://github.com/Instagram/LibCST), enabling precise analysis without executing code.

This tool helps ensure your Lambda function behaves correctly when SnapStart restores a pre-initialized execution environment.

---

# 🚀 Features

- 🔁 **Recursive repository scanning** (`**/*.py`)
- 🎯 **8 SnapStart-incompatibility rule categories**
- 💬 Supports multiple output formats:
  - `text`
  - `json`
  - `html` (interactive Jinja2 report)
- 🪶 Inline suppression with comments:
  - `# snapstart: ignore[PY001]`
- ⚙️ `.snapstart-scan.yaml` config support
- 📊 HTML report with filters + syntax-highlighted code context

---

# 📦 Installation

## Option 1 — Prebuilt Binary (Recommended)

Download from **GitHub Releases**.

```bash
chmod +x snapstart-scan
./snapstart-scan --repo /path/to/repo
```

➡️ **No Python required**.

---

## Option 2 — Run From Source

```bash
git clone https://github.com/vanshmadan/aws-lambda-snapstart-python-scanner.git
cd aws-lambda-snapstart-python-scanner

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run scanner:

```bash
python cli.py --repo /path/to/lambda
```

---

# 🕹️ Usage

### Basic scan

```bash
snapstart-scan --repo my-lambda-project
```
### Generate HTML report

```bash
snapstart-scan --repo . --format html
```

Output:

```
snapstart_report.html
```

---

# 📊 Supported Rules

| Rule | Description |
|------|-------------|
| PY001 | Mutable module‑level state |
| PY002 | Non‑idempotent logic at import time |
| PY003 | Threads/executors started at import |
| PY004 | Opening files/sockets at import |
| PY005 | Random/time/uuid executed at import |
| PY006 | `boto3.client()` during init |
| PY007 | Tempfiles, creds or FS access at import |
| PY008 | Dangerous init without restore hooks |

---

# 🖼️ Example Output

```
WARN PY001_MUTABLE_MODULE_STATE /app.py:4079
→ routers = [
   Mutable object created at module level; consider making immutable or moving to handler.

ERROR PY002_NON_IDEMPOTENT_INIT /test.py:7
→ requests.get("https://example.com")
   Potential non-idempotent side-effect call 'requests.get' at module import.
```

---

# 🎛️ Inline Suppression

### Ignore a specific rule

```python
routers = []  # snapstart: ignore[PY001]
```

### Ignore all on line

```python
value = generate_data()  # snapstart: ignore
```

---

# ⚙️ Configuration (`.snapstart-scan.yaml`)

```yaml
output_format: text

ignore_patterns:
  - "venv/**"
  - "tests/**"

severities:
  PY001_MUTABLE_MODULE_STATE: WARN
  PY002_NON_IDEMPOTENT_INIT: ERROR

hook_names:
  - after_restore
  - before_invoke

exit_on:
  - ERROR
```

---

Fail pipeline on ERRORs:

```bash
./snapstart-scan --repo . --exit-on ERROR
```

---

# 🪪 License (Apache 2.0)

```
Licensed under the Apache License, Version 2.0
http://www.apache.org/licenses/LICENSE-2.0
```

---

# 🤝 Contributing

PRs and issues are welcome!

---

# ⭐ Support

If you like this project, give it a **GitHub star** ❤️
