"""Merge rsoccer_raw.csv + rsoccer_extra.csv, run prelabeler, save final labeled CSV."""
import csv, re, pandas as pd
from pathlib import Path
from prelabel import label   # reuse the labeling function

raw   = pd.read_csv(Path(__file__).parent / "rsoccer_raw.csv")
extra = pd.read_csv(Path(__file__).parent / "rsoccer_extra.csv")

combined = pd.concat([raw, extra], ignore_index=True).drop_duplicates(subset="text")
print(f"Combined: {len(combined)} rows")

labels, notes = [], []
for _, row in combined.iterrows():
    lbl, note = label(row["text"], str(row.get("source", "post")))
    labels.append(lbl)
    notes.append(note)

combined["label"] = labels
combined["notes"] = notes

print("\nFull distribution (with skips):")
print(combined["label"].value_counts().to_string())

keep = combined[combined["label"] != "skip"].copy()

# Cap at 80 per label, prefer longer posts for analysis (more informative)
parts = []
for lbl, group in keep.groupby("label"):
    if lbl == "analysis":
        # Prefer longer posts for analysis — sort by text length descending
        group = group.copy()
        group["_len"] = group["text"].str.len()
        group = group.sort_values("_len", ascending=False).drop(columns="_len")
    sampled = group.head(80)
    parts.append(sampled)

final = pd.concat(parts).sample(frac=1, random_state=42).reset_index(drop=True)

print(f"\nFinal labeled distribution (capped at 80 per label):")
print(final["label"].value_counts().to_string())
print(f"Total: {len(final)}")

out = Path(__file__).parent / "rsoccer_labeled.csv"
final[["text", "label", "source", "notes"]].to_csv(out, index=False, quoting=csv.QUOTE_ALL)
print(f"\nSaved -> {out.name}")
