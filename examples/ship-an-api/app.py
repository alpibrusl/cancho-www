"""The 'app': a stand-in for whatever uses the service. It registers 200 users through the client that clientgen generated
(client.py), then lists them all. The client returns the dataclasses it annotates (User, Page), so the app reads
attributes, not keys. It writes two CSV files for the analytics steps: requests.csv (what each call got) and users.csv (what the service now holds). Synthetic users: fixed
formulas, no randomness; a few are invalid on purpose (an empty name, an age past 150) and a few are very old but valid.
Not cancho: this file is the only Python on the path, and it is the customer, not the product."""
import csv
import sys

import client

base = sys.argv[1]
api = client.Client(base)
roles = ["user", "user", "user", "guest", "admin"]
with open("requests.csv", "w", newline="") as out:
    log = csv.writer(out)
    log.writerow(["n", "status", "field"])
    for i in range(200):
        name = f"user{i:03d}"
        age = 18 + (i * 7) % 60
        if i % 50 == 0:
            age = 125 + i // 50           # very old, but valid today
        if i % 23 == 5:
            age = 151 + i % 9             # past the limit
        if i % 41 == 7:
            name = ""                     # too short
        try:
            api.createUser(body=client.NewUser(name=name, age=age, role=roles[i % 5]))
            log.writerow([i, 201, ""])
        except client.ProblemError as e:
            fields = ";".join(sorted(err["pointer"] for err in (e.problem.errors or [])))
            log.writerow([i, e.problem.status, fields])
page = api.listUsers(limit=100)
rows = list(page.items)
offset = 100
while len(rows) < page.total:
    rows += api.listUsers(limit=100, offset=offset).items
    offset += 100
with open("users.csv", "w", newline="") as out:
    w = csv.writer(out)
    w.writerow(["id", "name", "age", "role"])
    for u in rows:
        w.writerow([u["id"], u["name"], u.get("age", ""), u.get("role", "")])
print(f"registered {len(rows)} of 200 attempts")
