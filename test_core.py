import unittest
from pathlib import Path
from backend.utils.ingest import parse_csv
from backend.services.flow import circular_exchanges
from backend.services.summary import summarize

ROOT=Path(__file__).resolve().parents[1]
HEADER=b"id,sender,receiver,amount,timestamp,label\n"
THREE=b"a,X,Y,100,2026-01-01T00:00:00Z,1\nb,Y,Z,99,2026-01-01T00:10:00Z,1\nc,Z,X,98,2026-01-01T00:20:00Z,1\n"
EXTRA=b"d,U,V,12,2026-01-01T01:00:00Z,\ne,U,W,15,2026-01-02T00:00:00Z,0\n"


class Core(unittest.TestCase):
    def test_demo(self):
        rows=parse_csv((ROOT/"datasets/demo.csv").read_bytes())
        result=circular_exchanges(rows)
        self.assertEqual(len(result["groups"]),6)
        self.assertTrue(all(len(g)==3 for g in result["groups"]))
        self.assertGreaterEqual(len(result["flagged_ids"]),18)

    def test_loop(self):
        rows=parse_csv(HEADER+THREE+EXTRA)
        f=circular_exchanges(rows)
        self.assertEqual(f["groups"],[["X","Y","Z"]])
        self.assertEqual(f["rings"][0]["elapsed_minutes"],20)
        self.assertIsNone(rows[3]["label"])

    def test_no_loop_after_deadline(self):
        rows=parse_csv(HEADER+THREE.replace(b"00:20:",b"04:20:")+EXTRA)
        self.assertEqual(circular_exchanges(rows)["rings"],[])

    def test_invalid_input(self):
        for body in [HEADER+THREE,HEADER+THREE+EXTRA.replace(b"12,",b"nan,"),HEADER+THREE+EXTRA.replace(b"e,U",b"a,U"),b"amount\n0\n"]:
            with self.subTest(body=body),self.assertRaises(ValueError): parse_csv(body)

    def test_daily_weekly_monthly(self):
        rows=parse_csv(HEADER+THREE+EXTRA)
        for r in rows: r.update(risk="Low", flagged=False, reasons=[])
        for period,bins in [("daily",2),("weekly",1),("monthly",1)]:
            s=summarize(rows,[],[],{},period)
            self.assertEqual(len(s["series"]),bins)
            self.assertEqual(s["volume"],324)
            self.assertEqual(sum(x["count"] for x in s["series"]),5)

