"""Detect time-ordered three-transfer loops with approximately conserved value."""
from collections import defaultdict, deque
from datetime import datetime, timedelta


def circular_exchanges(rows, horizon=timedelta(hours=2)):
    incoming = defaultdict(deque)
    accounts, evidence, rings = {}, set(), []

    def recent(account, now):
        bucket = incoming[account]
        while bucket and now - bucket[0][0] > horizon:
            bucket.popleft()
        return bucket

    # A bounded lookback prevents dense fan-in datasets from exhausting a worker.
    for r in rows:
        now = datetime.fromisoformat(r["timestamp"])
        s, t = r["sender"], r["receiver"]
        for mid_time, middle in list(recent(s, now))[-64:]:
            if middle["sender"] in (s, t) or s == t or mid_time >= now:
                continue
            for first_time, first in reversed(list(recent(middle["sender"], now))[-64:]):
                if first["sender"] != t or first_time >= mid_time:
                    continue
                amounts = [v["amount"] for v in (first, middle, r)]
                if min(amounts) < .8 * max(amounts):
                    continue
                transfers = [first["id"], middle["id"], r["id"]]
                evidence.update(transfers)
                rings.append(dict(accounts=[t, middle["sender"], s], transactions=transfers,
                                  elapsed_minutes=round((now-first_time).total_seconds()/60,1)))
                break
            else:
                continue
            break
        recent(t, now).append((now, r))

    def root(a):
        accounts.setdefault(a, a)
        while a != accounts[a]:
            accounts[a] = accounts[accounts[a]]
            a = accounts[a]
        return a

    for ring in rings:
        a,b,c = ring["accounts"]
        accounts[root(b)] = root(a)
        accounts[root(c)] = root(a)
    groups = defaultdict(list)
    for a in accounts:
        groups[root(a)].append(a)
    return {"rings": rings, "flagged_ids": sorted(evidence),
            "groups": sorted([sorted(v) for v in groups.values()])}

