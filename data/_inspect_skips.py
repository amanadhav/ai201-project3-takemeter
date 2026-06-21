import pandas as pd
import re

df = pd.read_csv("data/rsoccer_raw.csv")

def skip_reason(text, source):
    t = str(text).strip()
    tl = t.lower()
    tln = len(t)
    if tln > 1500 and any(k in tl for k in ["auto-refreshing","line-ups","starting xi","subs:","substitution, "]):
        return "match_thread_body"
    if tln > 1000 and "match stats" in tl and "possession" in tl and "shots on goal" in tl:
        return "post_match_thread_body"
    if re.match(r'^\[.{1,60}\]\s', t) and tln < 300:
        return "news_post"
    if any(k in tl for k in ["tickets available", "for sale", "ebay", "pixel cleaning"]):
        return "commercial"
    if re.match(r'^match thread:', t, re.IGNORECASE) and tln < 300:
        return "match_thread_header"
    if tln > 5000:
        return "too_long_article"
    if "what to watch this week" in tl and tln > 500:
        return "schedule_post"
    return None

df["skip_reason"] = df.apply(lambda r: skip_reason(r["text"], r.get("source","post")), axis=1)
skipped = df[df["skip_reason"].notna()]
print("Skip breakdown:")
print(skipped["skip_reason"].value_counts())
print()
print("too_long_article posts:")
for _, row in skipped[skipped["skip_reason"]=="too_long_article"].iterrows():
    print(f"  len={len(row['text'])} | {row['text'][:100]}")
print()
print("Total skipped:", len(skipped))
print("Total kept:   ", len(df) - len(skipped))
