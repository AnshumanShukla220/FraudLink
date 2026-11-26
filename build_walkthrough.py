"""Generate a portable evidence walkthrough from the same temporal detector as the API."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.utils.ingest import parse_csv
from backend.services.flow import circular_exchanges

rows = parse_csv((ROOT / "datasets/demo.csv").read_bytes())
found = circular_exchanges(rows)
payload = dict(total=len(rows), volume=round(sum(r["amount"] for r in rows),2), **found,
               evidence={r["id"]:r for r in rows if r["id"] in found["flagged_ids"]})
template = (ROOT / "documentation/walkthrough.template").read_text(encoding="utf-8")
(ROOT / "OPEN-DEMO.html").write_text(template.replace("__DATA__",json.dumps(payload).replace("<","\\u003c")),encoding="utf-8")
print(f'{len(rows)} transactions; {len(found["groups"])} chronological ring groups; {len(found["flagged_ids"])} distinct evidence transfers.')

