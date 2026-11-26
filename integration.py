"""Run against a fresh local demo stack. Upload replaces the active demo dataset."""
import io
import csv
import json
import sys
import time
import urllib.request as http
from pathlib import Path
from urllib.error import HTTPError

ROOT=Path(__file__).resolve().parents[1]
BASE="http://127.0.0.1:8080"


def request(path, method="GET", body=None, mime="application/json"):
    if isinstance(body,dict): body=json.dumps(body).encode()
    return http.urlopen(http.Request(BASE+path,data=body,method=method,headers={"Content-Type":mime}),timeout=180).read()


def api(path,*args): return json.loads(request("/api"+path,*args))


if __name__=="__main__":
    assert "FraudLink" in request("/").decode()
    if api("/dashboard/stats")["dataset"]!="demo.csv":
        sys.exit("Use an isolated demo stack; active dataset differs from demo.csv.")
    raw=(ROOT/"datasets/demo.csv").read_bytes()
    boundary="FraudLinkDemoBoundary"
    body=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="demo.csv"\r\nContent-Type: text/csv\r\n\r\n'.encode()+raw+f'\r\n--{boundary}--\r\n'.encode())
    imported=api("/transactions/upload","POST",body,"multipart/form-data; boundary="+boundary)
    assert imported["count"]==sum(1 for _ in csv.DictReader(io.StringIO(raw.decode())))
    initial=api("/dashboard/stats")
    assert initial["run"]==imported["run"]
    api("/fraud/detect","POST")
    assert api("/clusters/generate","POST")["clusters"]>0
    stats=api("/dashboard/stats")
    graph=api("/network/graph")
    clusters=api("/clusters")
    assert stats["total"]==imported["count"] and stats["flagged"]==len(api("/alerts"))
    assert stats["clusters"]==len(clusters) and len(graph["nodes"])==len(api("/accounts"))
    assert sum(e["count"] for e in graph["edges"])==stats["total"]
    alert=api("/alerts")[0]
    tx=api("/transactions/"+alert["transaction"])
    assert tx["flagged"] and tx["risk"] in ("High","Critical")
    assert api("/transactions?q="+tx["id"])["total"]==1
    case=api("/cases","POST",{"title":"Demo transfer review","account":tx["sender"],"evidence":[tx["id"]]})
    edit={"notes":"Reviewed sender relationships and timeline.","status":"In review","revision":1,"evidence":[tx["id"]]}
    api("/cases/"+case["id"],"PATCH",edit)
    try: api("/cases/"+case["id"],"PATCH",edit)
    except HTTPError as e: assert e.code==409
    else: raise AssertionError("Stale edit accepted")
    assert api("/cases/"+case["id"])["timeline"]
    assert request("/api/cases/"+case["id"]+"/pdf").startswith(b"%PDF")
    for p in ["daily","weekly","monthly"]:
        assert api("/reports?period="+p)["total"]==stats["total"]
        assert request("/api/reports/export?period="+p).startswith(b"day,count,flagged,volume")
    print(f'PASS: {stats["total"]} transfers, {stats["flagged"]} flagged, {len(clusters)} clusters, case {case["id"]}.')

