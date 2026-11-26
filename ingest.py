import csv
import io
import math
import re
from datetime import datetime, timezone

FIELDS = {"id", "sender", "receiver", "amount", "timestamp"}
IDENT = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")


def parse_csv(raw):
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    if not FIELDS.issubset(reader.fieldnames or []):
        raise ValueError("Required columns: id, sender, receiver, amount, timestamp")
    records, seen = [], set()
    for line, row in enumerate(reader, 2):
        try:
            record = {k: row[k].strip() for k in FIELDS}
            if not all(IDENT.fullmatch(record[k]) for k in ("id", "sender", "receiver")):
                raise ValueError("Invalid or missing identifier")
            if record["id"] in seen:
                raise ValueError("Duplicate transaction ID")
            seen.add(record["id"])
            amount = float(record["amount"])
            if not math.isfinite(amount) or not .01 <= amount <= 1e12:
                raise ValueError("Amount must be at least one cent and at most 1 trillion")
            when = datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00"))
            when = when.replace(tzinfo=when.tzinfo or timezone.utc).astimezone(timezone.utc)
            label = (row.get("label") or "").strip()
            if label not in ("", "0", "1"):
                raise ValueError("Label must be blank, 0 or 1")
            records.append(dict(record, amount=round(amount, 2), timestamp=when.isoformat(),
                                label=int(label) if label else None))
        except (ValueError, AttributeError, TypeError) as exc:
            raise ValueError(f"Row {line}: {exc}") from exc
        if len(records) > 10000:
            raise ValueError("Maximum dataset size is 10,000 transactions")
    if len(records) < 5:
        raise ValueError("At least five transactions are required")
    return sorted(records, key=lambda r: (r["timestamp"], r["id"]))

