import csv
import io
import uuid
from datetime import date, datetime, timezone
from typing import Literal
from xml.sax.saxutils import escape
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from ..database.store import active, db, items, publish
from ..ml.engine import analyze
from ..models.cases import CaseCreate, CaseUpdate
from ..services.summary import summarize
from ..utils.ingest import parse_csv

router=APIRouter(prefix="/api")
Period=Literal["daily","weekly","monthly"]


def one(name, key, run):
    record=db[name].find_one({"id":key,"run":run},{"_id":0,"run":0})
    if not record: raise HTTPException(404,"Record was not found in this analysis")
    return record


@router.get("/dashboard/stats")
@router.get("/reports")
def stats(period:Period="daily"):
    h=active()
    return dict(**summarize(items("transactions",h["run"]),items("accounts",h["run"]),items("clusters",h["run"]),h["metrics"],period),
                dataset=h["filename"],updated=h["updated"],run=h["run"])


@router.post("/transactions/upload")
def upload(file:UploadFile=File(...)):
    raw=file.file.read(4_000_001)
    if len(raw)>4_000_000: raise HTTPException(413,"Maximum file size is 4 MB")
    try: rows=parse_csv(raw)
    except (ValueError,csv.Error) as e: raise HTTPException(422,str(e))
    data,model=analyze(rows)
    return {"run":publish(data,model,(file.filename or "dataset.csv")[:150]),"count":len(rows)}


@router.get("/transactions")
def transactions(q:str="",risk:Literal["Low","Medium","High","Critical"]|None=None,
                 minimum:float|None=Query(None,ge=0),maximum:float|None=Query(None,ge=0),
                 start:date|None=None,end:date|None=None,page:int=Query(1,ge=1),size:int=Query(25,ge=1,le=100),download:bool=False):
    rows=items("transactions",active()["run"])
    if minimum is not None and maximum is not None and maximum<minimum: raise HTTPException(422,"Amount range is reversed")
    if start and end and end<start: raise HTTPException(422,"Date range is reversed")
    rows=[r for r in reversed(rows) if (not risk or r["risk"]==risk) and
          any(q.lower() in r[k].lower() for k in ("id","sender","receiver")) and
          (minimum is None or r["amount"]>=minimum) and (maximum is None or r["amount"]<=maximum)
          and (not start or r["timestamp"][:10]>=str(start)) and (not end or r["timestamp"][:10]<=str(end))]
    if download: return csv_result(rows,["id","sender","receiver","timestamp","amount","risk","score","flagged"],"transactions")
    return dict(items=rows[(page-1)*size:page*size],total=len(rows))


@router.get("/transactions/{key}")
def transaction(key:str): return one("transactions",key,active()["run"])


@router.post("/fraud/detect")
@router.post("/clusters/generate")
def refresh():
    h=active()
    data,model=analyze(items("transactions",h["run"]))
    return {"run":publish(data,model,h["filename"]),"clusters":len(data["clusters"])}


@router.get("/clusters")
def clusters(): return items("clusters",active()["run"])


@router.get("/clusters/{key}")
def cluster(key:str): return one("clusters",key,active()["run"])


@router.get("/accounts")
def accounts(): return sorted(items("accounts",active()["run"]),key=lambda a:-a["score"])


@router.get("/alerts")
def alerts(): return items("alerts",active()["run"])


@router.get("/network/graph")
def network():
    run=active()["run"]
    return dict(nodes=items("accounts",run),edges=items("edges",run))


def evidence(ids,account,run):
    for key in set(ids):
        r=one("transactions",key,run)
        if account not in (r["sender"],r["receiver"]): raise HTTPException(422,"Evidence must involve the case account")


@router.post("/cases",status_code=201)
def open_case(body:CaseCreate):
    run=active()["run"]
    a=one("accounts",body.account,run)
    evidence(body.evidence,body.account,run)
    record=dict(**body.model_dump(),id="FL-"+uuid.uuid4().hex[:12].upper(),risk=a["risk"],status="Open",
                created=datetime.now(timezone.utc).isoformat(),revision=1,run=run)
    db.cases.insert_one(record)
    record.pop("_id")
    return record


@router.get("/cases")
def cases(): return list(db.cases.find({},{"_id":0}).sort("created",-1))


def get_case(key):
    c=db.cases.find_one({"id":key},{"_id":0})
    if not c: raise HTTPException(404,"Case not found")
    return c


@router.get("/cases/{key}")
def case_detail(key:str):
    c=get_case(key)
    timeline=items("transactions",c["run"],{"$or":[{"sender":c["account"]},{"receiver":c["account"]}]})
    return dict(**c,timeline=timeline,account_detail=one("accounts",c["account"],c["run"]))


@router.patch("/cases/{key}")
def update_case(key:str,body:CaseUpdate):
    c=get_case(key)
    evidence(body.evidence,c["account"],c["run"])
    result=db.cases.update_one({"id":key,"revision":body.revision},{"$set":body.model_dump(exclude={"revision"}),"$inc":{"revision":1}})
    if not result.modified_count: raise HTTPException(409,"Another analyst edited this case. Reopen it and retry.")
    return get_case(key)


def csv_result(rows,fields,name):
    out=io.StringIO()
    writer=csv.DictWriter(out,fieldnames=fields,extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({k:("'"+str(row[k]) if str(row[k]).startswith(("=","+","-","@")) else row[k]) for k in fields})
    return Response(out.getvalue(),media_type="text/csv",headers={"Content-Disposition":f'attachment; filename="{name}.csv"'})


def pdf(title,lines):
    out=io.BytesIO()
    styles=getSampleStyleSheet()
    story=[Paragraph(escape(title),styles["Title"]),Spacer(1,15)]
    story.extend(Paragraph(escape(str(line)),styles["BodyText"]) for line in lines)
    SimpleDocTemplate(out).build(story)
    return Response(out.getvalue(),media_type="application/pdf",headers={"Content-Disposition":'attachment; filename="fraudlink-report.pdf"'})


@router.get("/cases/{key}/pdf")
def case_pdf(key:str):
    c=case_detail(key)
    return pdf("FraudLink investigation "+key,[c["title"],f'{c["account"]} | {c["risk"]} risk | {c["status"]}',c["notes"],"Evidence",
               *[f'{r["id"]} | {r["timestamp"]} | {r["sender"]} to {r["receiver"]} | {r["amount"]} USD | {r["risk"]}' for r in c["timeline"] if r["id"] in c["evidence"]]])


@router.get("/reports/export")
def report(period:Period="daily",format:Literal["csv","pdf"]="csv"):
    s=stats(period)
    if format=="csv": return csv_result(s["series"],["day","count","flagged","volume"],"fraudlink-"+period)
    return pdf("FraudLink "+period+" report",[s["dataset"],f'{s["total"]} transactions | {s["flagged"]} flagged | {s["clusters"]} clusters',
               *[f'{r["day"]} | {r["count"]} transactions | {r["flagged"]} flagged | USD {r["volume"]:,.2f}' for r in s["series"]]])

