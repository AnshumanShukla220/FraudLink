from collections import Counter
from datetime import datetime
import math
import networkx as nx
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score

from ..services.flow import circular_exchanges

FEATURES = ["Log amount", "Daily sends", "Pair frequency", "Beneficiaries", "Funding sources", "Cycle membership"]


def analyze(rows):
    rows = sorted(rows, key=lambda r: (r["timestamp"], r["id"]))
    traced = circular_exchanges(rows)
    timed_ids = set(traced["flagged_ids"])
    g = nx.DiGraph()
    pairs = Counter((r["sender"], r["receiver"]) for r in rows)
    g.add_edges_from(pairs)
    daily = Counter((r["sender"], r["timestamp"][:10]) for r in rows)
    comp = {a: i for i, members in enumerate(nx.strongly_connected_components(g)) for a in members}
    vectors, reasons = [], []
    for r in rows:
        s, t = r["sender"], r["receiver"]
        cycle = comp[s] == comp[t]
        freq = daily[s, r["timestamp"][:10]]
        vectors.append([math.log1p(r["amount"]), freq, pairs[s,t], g.out_degree(s), g.in_degree(t), int(cycle)])
        why = []
        if cycle: why.append("Circular transfers")
        if pairs[s,t] >= 3: why.append("Repeated connection")
        if g.out_degree(s) >= 4: why.append("One-to-many transfers")
        if g.in_degree(t) >= 4: why.append("Many-to-one transfers")
        if freq >= 4: why.append("Elevated daily frequency")
        reasons.append(why)
    frame = pd.DataFrame(vectors, columns=FEATURES)
    medians = frame.median()
    scaler = StandardScaler()
    x = scaler.fit_transform(frame.fillna(medians))
    forest = IsolationForest(n_estimators=120, random_state=42).fit(x)
    raw = -forest.score_samples(x)
    density = DBSCAN(eps=.85, min_samples=4).fit_predict(x)
    # Attribute score sensitivity by replacing each feature with its median.
    importance = []
    for i, feature in enumerate(FEATURES):
        changed = x.copy()
        changed[:, i] = np.median(x[:, i])
        importance.append({"name": feature, "value": round(float(np.mean(np.abs(raw + forest.score_samples(changed)))),5)})
    suspicious = nx.Graph()
    accounts, alerts = {}, []
    for i, r in enumerate(rows):
        why = reasons[i]
        score = float(np.clip((raw[i]-.32)*1.65 + .18*vectors[i][-1] + .05*(density[i]==-1), 0, 1))
        if r["id"] in timed_ids:
            score = max(score, .8)
            why.insert(0, "Time-ordered circular exchange")
        risk = "Critical" if score>=.78 else "High" if score>=.60 else "Medium" if score>=.36 else "Low"
        flag = risk in ("High","Critical")
        if density[i] == -1: why.append("Sparse behavioral neighborhood")
        r.update(score=round(score,4), risk=risk, flagged=flag, reasons=why or ["Typical observed activity"], behavior=int(density[i]))
        if flag:
            suspicious.add_edge(r["sender"],r["receiver"])
            alerts.append(dict(id="AL-"+r["id"], transaction=r["id"], timestamp=r["timestamp"], risk=risk, title=r["reasons"][0], account=r["sender"], score=r["score"]))
        for a in set([r["sender"],r["receiver"]]):
            old=accounts.setdefault(a,dict(id=a, score=0, risk="Low", count=0, volume=0, cluster=None))
            old["count"]+=1
            old["volume"]=round(old["volume"]+r["amount"],2)
            if r["score"]>=old["score"]: old.update(score=r["score"],risk=risk)
    clusters=[]
    for group in sorted(nx.connected_components(suspicious),key=lambda m:(-len(m),min(m))):
        cid=f"CL-{len(clusters)+1:03d}"
        for a in group: accounts[a]["cluster"]=cid
        clusters.append(dict(id=cid, members=sorted(group),size=len(group),score=max(accounts[a]["score"] for a in group)))
    edges=[]
    for (s,t),count in pairs.items():
        edges.append(dict(source=s,target=t,count=count,transactions=[]))
    lookup={(e["source"],e["target"]):e for e in edges}
    for r in rows: lookup[r["sender"],r["receiver"]]["transactions"].append(r["id"])
    for c in clusters:
        members=set(c["members"])
        c["patterns"]=dict(Counter(p for r in rows if r["flagged"] and r["sender"] in members for p in r["reasons"]))
        sub=g.subgraph(members)
        c["chains"]=[p for s in sorted(members) for p in list(nx.single_source_shortest_path(sub,s,cutoff=3).values()) if len(p)>=3][:20] if len(members)<=100 else []
    labeled=[r for r in rows if r["label"] is not None]
    metrics={"labeled":len(labeled),"recall":None,"precision":None,"importance":importance}
    if labeled:
        y=[r["label"] for r in labeled]
        pred=[r["flagged"] for r in labeled]
        if sum(y): metrics["recall"]=float(recall_score(y,pred))
        if sum(pred): metrics["precision"]=float(precision_score(y,pred))
    return dict(transactions=rows,accounts=list(accounts.values()),clusters=clusters,alerts=alerts[::-1],edges=edges,metrics=metrics), dict(model=forest,scaler=scaler,medians=medians,features=FEATURES)

