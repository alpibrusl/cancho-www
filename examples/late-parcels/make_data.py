"""The data for the late-parcels example: 400 parcels for a small courier, and 300 from the next month, synthetic. Fixed formulas, no randomness, so the
file is the same every time. A parcel is late when its trip score crosses a line; three distances are left empty on
purpose (a scanner that did not read). Not real data, and nothing here measures a real courier."""
rows = ["distance_km,hour,rain,late"]
for i in range(400):
    distance = round(2 + (i * 37) % 180 / 4 + (i % 7) * 0.3, 1)
    hour = 7 + (i * 5) % 13
    rain = 1 if (i * 11) % 9 < 3 else 0
    score = 0.08 * distance + 1.1 * rain + (0.7 if hour >= 16 else 0) + ((i * 13) % 10) * 0.12
    late = 1 if score > 3.9 else 0
    rows.append(f"{distance},{hour},{rain},{late}")
for n in (40, 171, 322):
    d, h, r, l = rows[n].split(",")
    rows[n] = f",{h},{r},{l}"
open("parcels.csv", "w").write("\n".join(rows) + "\n")
print("wrote parcels.csv:", len(rows) - 1, "rows")

# The next month is the rainy season: longer trips, more rain, and rain delays a parcel more than it used to.
# The line for "late" is the same; the world moved, the model did not.
nxt = ["distance_km,hour,rain,late"]
for i in range(300):
    distance = round(6 + (i * 41) % 190 / 3.2 + (i % 5) * 0.4, 1)
    hour = 7 + (i * 7) % 13
    rain = 1 if (i * 13) % 10 < 6 else 0
    score = 0.08 * distance + 1.9 * rain + (0.7 if hour >= 16 else 0) + ((i * 17) % 10) * 0.12
    nxt.append(f"{distance},{hour},{rain},{1 if score > 3.9 else 0}")
open("next.csv", "w").write("\n".join(nxt) + "\n")
print("wrote next.csv:", len(nxt) - 1, "rows")
