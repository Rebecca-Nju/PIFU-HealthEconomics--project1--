# analysis/check_codelists_and_run.py
# Minimal codelist checker

import re, pandas as pd
from pathlib import Path

codefile = Path("analysis") / "codelists.py"
if not codefile.exists():
    print("❌ analysis/codelists.py not found.")
    raise SystemExit

text = codefile.read_text(encoding="utf-8")
paths = re.findall(r"codelist_from_csv\(\s*['\"]([^'\"]+)['\"]", text)

if not paths:
    print("No codelists found.")
    raise SystemExit

print("Checking codelists...\n")
for raw in paths:
    p = Path(raw)
    if not p.exists():
        # try common relative locations
        alt = Path("analysis") / "codelists" / p.name
        p = alt if alt.exists() else p
    if not p.exists():
        print(f"🚫 Missing: {p}")
        continue
    try:
        df = pd.read_csv(p, nrows=3)
        print(f"✅ {p} — {len(df.columns)} columns → {list(df.columns)}")
    except Exception as e:
        print(f"⚠️  Couldn’t read {p}: {e}")

print("\nDone.")
