"""The data for the shop-energy example: a small shop, 120 hours, synthetic. Fixed formulas, no randomness, so the file
is the same every time. Three cells are left empty on purpose (a sensor that dropped out): that is the dirt the roles pass
around. Not real data, and nothing here measures a real shop."""
rows = ["hour,outside_c,open,kwh"]
for i in range(120):
    hour = i % 24
    outside = round(8 + 9 * (1 if 10 <= hour <= 17 else 0.2) + (i // 24) * 0.7 + ((i * 7) % 5) * 0.3, 1)
    is_open = 1 if 9 <= hour <= 19 else 0
    kwh = round(1.2 + 3.1 * is_open + 0.18 * max(outside - 16, 0) + 0.12 * max(14 - outside, 0) + ((i * 13) % 7) * 0.05, 2)
    rows.append(f"{hour},{outside},{is_open},{kwh}")
for n in (17, 58, 101):  # sensor dropouts
    h, o, p, k = rows[n].split(",")
    rows[n] = f"{h},{o},{p},"
open("shop.csv", "w").write("\n".join(rows) + "\n")
print("wrote shop.csv:", len(rows) - 1, "rows")
