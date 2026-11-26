import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
import joblib
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError

db = MongoClient(os.getenv("MONGO_URI","mongodb://localhost:27017"), serverSelectionTimeoutMS=5000).get_database("fraudlink")


def setup():
    for name in ("transactions","accounts","clusters","alerts","edges"):
        db[name].create_index([("run",ASCENDING),("id",ASCENDING)])
    db.cases.create_index("id", unique=True)


def active():
    head = db.state.find_one({"_id":"active"})
    if not head: raise RuntimeError("No analyzed dataset")
    return head


def publish(data, model, filename, initial=False):
    run=uuid.uuid4().hex
    folder=Path(os.getenv("MODEL_DIR","model_store"))
    folder.mkdir(parents=True,exist_ok=True)
    joblib.dump(model,folder / f"{run}.joblib")
    for name in ("transactions","accounts","clusters","alerts","edges"):
        if data[name]: db[name].insert_many([dict(record,run=run) for record in data[name]])
    head=dict(run=run,filename=filename,metrics=data["metrics"],updated=datetime.now(timezone.utc).isoformat())
    db.runs.insert_one(dict(head))
    if initial:
        try: db.state.insert_one(dict(head,_id="active"))
        except DuplicateKeyError: pass
    else: db.state.replace_one({"_id":"active"},dict(head,_id="active"),upsert=True)
    return run


def items(name,run,query=None):
    cursor = db[name].find(dict(query or {},run=run),{"_id":0,"run":0})
    if name in ("alerts", "transactions"):
        order = -1 if name == "alerts" else 1
        cursor = cursor.sort([("timestamp", order), ("id", order)])
    return list(cursor)

