"""
collect_rsoccer.py
------------------
Pulls posts and comments from r/soccer using the Arctic Shift API
(free, open Reddit archive — no account or API key required).

OUTPUT:
  data/rsoccer_raw.csv  — text column filled, label column blank.
  Open the file, fill in the 'label' column for each row:
    analysis | hot_take | reaction
  Then save as data/rsoccer_labeled.csv before running the notebook.

Usage:
    pip install requests pandas
    python data/collect_rsoccer.py
"""

import csv
import time
import requests
import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE     = "https://arctic-shift.photon-reddit.com/api"
SUB      = "soccer"
OUT      = Path(__file__).parent / "rsoccer_raw.csv"
HEADERS  = {"User-Agent": "takemeter-data-collector/1.0 (academic project)"}
MIN_LEN  = 40

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fetch(endpoint, params):
    url = f"{BASE}/{endpoint}"
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=20)
            r.raise_for_status()
            return r.json().get("data") or []
        except Exception as e:
            print(f"    retry {attempt+1}: {e}")
            time.sleep(3)
    return []


def clean(text):
    return " ".join(str(text or "").split())


def is_match_thread(title):
    kw = ["match thread", "post match", "pre-match", "post-match",
          "half time", "half-time", "[ft]", "ft |", "ft:"]
    t = title.lower()
    return any(k in t for k in kw)


def unix_days_ago(days):
    return int(time.time()) - days * 86400

# ---------------------------------------------------------------------------
# Collectors
# ---------------------------------------------------------------------------

def collect_posts():
    """
    Fetch posts across multiple time windows to capture variety:
      - recent posts  -> reactions, quick takes
      - older window  -> more analytical pieces that accumulated discussion
    Uses sort=desc (by created_utc) within each window.
    """
    windows = [
        ("last 7 days",    unix_days_ago(7),   unix_days_ago(0)),
        ("7-30 days ago",  unix_days_ago(30),  unix_days_ago(7)),
        ("30-90 days ago", unix_days_ago(90),  unix_days_ago(30)),
        ("90-180 days ago",unix_days_ago(180), unix_days_ago(90)),
    ]

    seen, rows = set(), []

    for label, after, before in windows:
        print(f"  Posts [{label}]...")
        items = fetch("posts/search", {
            "subreddit": SUB,
            "limit":     100,
            "sort":      "desc",
            "after":     after,
            "before":    before,
        })
        new = 0
        for p in items:
            pid = p.get("id", "")
            if pid in seen:
                continue
            seen.add(pid)

            title    = clean(p.get("title", ""))
            selftext = clean(p.get("selftext", ""))

            if selftext and selftext not in ("[deleted]", "[removed]"):
                text = f"{title} -- {selftext}"
            else:
                text = title

            if len(text) < MIN_LEN:
                continue

            rows.append({"text": text, "label": "", "source": "post"})
            new += 1
        print(f"    -> {new} new posts (total so far: {len(rows)})")
        time.sleep(0.8)

    return rows


def collect_comments():
    """
    Pull comments from two types of threads:
      - match threads       -> almost always 'reaction'
      - high-comment posts  -> mix of hot_take and reaction
    """
    rows = []
    print("\n  Finding threads for comment collection...")

    # Get post listing to find match threads and high-comment posts
    posts = fetch("posts/search", {
        "subreddit": SUB,
        "limit":     100,
        "sort":      "desc",
        "after":     unix_days_ago(30),
    })

    match_ids = [p["id"] for p in posts if is_match_thread(p.get("title", ""))][:8]
    discuss_ids = [
        p["id"] for p in posts
        if not is_match_thread(p.get("title", ""))
        and int(p.get("num_comments", 0)) > 150
    ][:6]

    print(f"  Found {len(match_ids)} match threads, {len(discuss_ids)} discussion posts")

    for src, post_ids, limit in [
        ("match_thread_comment",  match_ids,   25),
        ("discussion_comment",    discuss_ids, 15),
    ]:
        for pid in post_ids:
            comments = fetch("comments/search", {
                "link_id": f"t3_{pid}",
                "limit":   limit,
                "sort":    "desc",
            })
            added = 0
            for c in comments:
                body = clean(c.get("body", ""))
                if len(body) < MIN_LEN or body in ("[deleted]", "[removed]"):
                    continue
                rows.append({"text": body, "label": "", "source": src})
                added += 1
            if added:
                print(f"    post {pid}: +{added} comments ({src})")
            time.sleep(0.5)

    print(f"  -> {len(rows)} comments total")
    return rows

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 55)
    print("TakeMeter -- r/soccer data collector")
    print("Source: Arctic Shift API (no login needed)")
    print("=" * 55)

    post_rows    = collect_posts()
    comment_rows = collect_comments()

    all_rows = post_rows + comment_rows
    df = pd.DataFrame(all_rows, columns=["text", "label", "source"])
    df = df.drop_duplicates(subset="text").reset_index(drop=True)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    df.to_csv(OUT, index=False, quoting=csv.QUOTE_ALL)

    print()
    print("=" * 55)
    print(f"Saved {len(df)} examples -> {OUT.name}")
    print()
    print("Source breakdown:")
    hints = {
        "post":                  "mixed -- read for all 3 labels",
        "match_thread_comment":  "almost always reaction -- label fast",
        "discussion_comment":    "hot_take / reaction mix",
    }
    for src, count in df["source"].value_counts().items():
        print(f"  {src:<30} {count:>4}   {hints.get(src,'')}")
    print("=" * 55)
    print()
    print("NEXT STEPS:")
    print("  1. Open data/rsoccer_raw.csv in Excel or a text editor")
    print("  2. Fill the 'label' column for each row:")
    print("       analysis  -- structured argument with specific evidence")
    print("       hot_take  -- bold opinion asserted without evidence")
    print("       reaction  -- emotional response to a specific event")
    print("  3. Label at least 200 rows; aim for ~65-70 per label")
    print("  4. Delete the 'source' column, save as rsoccer_labeled.csv")
    print()
    print("TIP: Sort by 'source' to batch-label by type.")
    print("     match_thread_comment rows are almost always 'reaction'.")


if __name__ == "__main__":
    main()
