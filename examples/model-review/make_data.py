"""The data for the model-review example: 600 customers of a small subscription service, synthetic. Fixed formulas, no
randomness, so the files are the same every time. A customer churns when a score crosses a line. `train.csv` is the first
400 customers, `holdout.csv` the last 200 (customers the model has never been judged on), and `candidate_train.csv` is the
file a teammate trained a new model on: the training rows plus 80 of the holdout customers, which is the mistake the
review finds. Not real data, and nothing here measures a real service."""
head = "id,tenure_months,monthly_spend,tickets_90d,churned"
rows = []
for i in range(1, 601):
    tenure = 1 + (i * 7) % 60
    spend = round(9 + (i * 13) % 70 + (i % 5) * 0.5, 1)
    tickets = (i * 5) % 7 if i % 3 else (i * 3) % 5
    score = 2.2 - 0.045 * tenure + 0.35 * tickets + 0.012 * spend + ((i * 29) % 11) * 0.09 - 0.5
    rows.append((i, f"{i},{tenure},{spend},{tickets},{1 if score > 2.0 else 0}"))
train = [r for n, r in rows if n <= 400]
holdout = [r for n, r in rows if n > 400]
leaked = [r for n, r in rows if 401 <= n <= 480]
for name, body in (("train.csv", train), ("holdout.csv", holdout), ("candidate_train.csv", train + leaked)):
    open(name, "w").write(head + "\n" + "\n".join(body) + "\n")
    print("wrote", name, len(body), "rows")
