import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

rng = random.Random(1709)
start = datetime(2026, 10, 1, tzinfo=timezone.utc)
rows = []


def add(day, sender, receiver, amount, label, minute=None):
    time = start + timedelta(days=day, minutes=rng.randrange(1440) if minute is None else minute)
    rows.append([f"TX-{len(rows)+10001}", sender, receiver, amount, time.isoformat(), label])


for day in range(31):
    for _ in range(rng.randint(19, 47)):
        user = rng.randrange(200)
        add(day, f"AC-{2000+user}", f"AC-{3000+rng.randrange(70)}", round(rng.lognormvariate(5.6, .9), 2), 0)
for group, day in enumerate([4, 9, 14, 21, 26, 30]):
    ids = [f"AC-{7100+group*10+i}" for i in range(5)]
    for i in range(15):
        add(day, ids[i%5], ids[(i+1)%5], 4800+rng.randrange(750), 1, 600+i*3)
    for i in range(1, 5):
        add(day, ids[i], ids[0], 6400+rng.randrange(900), 1, 700+i)
    for i in range(3):
        add(day, ids[i], ids[(i+1)%3], 7200-i*35, 1, 900+i*5)
with Path(__file__).with_name("demo.csv").open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "sender", "receiver", "amount", "timestamp", "label"])
    writer.writerows(rows)

