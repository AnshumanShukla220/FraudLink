from collections import Counter, defaultdict
from datetime import date,timedelta


def summarize(rows, accounts, clusters, metrics, period="daily"):
    series=defaultdict(lambda:dict(count=0,flagged=0,volume=0))
    risk=Counter()
    for r in rows:
        d=date.fromisoformat(r["timestamp"][:10])
        if period=="weekly": d-=timedelta(days=d.weekday())
        if period=="monthly": d=d.replace(day=1)
        b=series[d.isoformat()]
        b["count"]+=1
        b["flagged"]+=int(r["flagged"])
        b["volume"]=round(b["volume"]+r["amount"],2)
        risk[r["risk"]]+=1
    return dict(total=len(rows), flagged=sum(r["flagged"] for r in rows), volume=round(sum(r["amount"] for r in rows),2),
                high=sum(a["risk"] in ["High","Critical"] for a in accounts),clusters=len(clusters),accounts=len(accounts),
                risk=risk,series=[dict(day=k,**series[k]) for k in sorted(series)],metrics=metrics,
                patterns=Counter(p for r in rows if r["flagged"] for p in r["reasons"]),
                sizes=[dict(name=c["id"],value=c["size"]) for c in clusters])

