"""
collect_rsoccer.py
------------------
Pulls posts and comments from r/soccer using the official Reddit API via PRAW.

SETUP (one-time, 2 minutes):
  1. Go to https://www.reddit.com/prefs/apps
  2. Scroll to the bottom, click "create another app"
  3. Fill in:
       Name: takemeter-collector  (anything works)
       Type: select "script"
       Redirect URI: http://localhost:8080
  4. Click "create app"
  5. Copy the CLIENT_ID (short string under the app name)
     and CLIENT_SECRET (the "secret" field)
  6. Paste them into the variables below (or use a .env file)

OUTPUT:
  data/rsoccer_raw.csv  — text column filled, label column empty.
  Open that file, read each row, and fill in the label column:
    analysis | hot_take | reaction

Usage:
    pip install praw pandas
    python data/collect_rsoccer.py

Requirements:
    pip install praw pandas
"""

import csv
import time
import praw
import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# Reddit API credentials — fill these in before running
# ---------------------------------------------------------------------------

CLIENT_ID     = "YOUR_CLIENT_ID"       # short string under app name
CLIENT_SECRET = "YOUR_CLIENT_SECRET"   # "secret" field in the app
USER_AGENT    = "takemeter-collector/1.0 by YOUR_REDDIT_USERNAME"

# Optional: set these to fetch user-specific data or avoid read-only limits
# Leave as empty strings to use read-only mode (no login required).
REDDIT_USERNAME = ""
REDDIT_PASSWORD = ""

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OUT_PATH         = Path(__file__).parent / "rsoccer_raw.csv"
SUBREDDIT        = "soccer"
POSTS_PER_FEED   = 100       # max Reddit allows per request
COMMENTS_PER_THREAD = 20     # top-level comments per match thread
MIN_TEXT_LEN     = 40        # skip very short posts

# ---------------------------------------------------------------------------
# Build the PRAW client
# ---------------------------------------------------------------------------

def build_reddit() -> praw.Reddit:
    if REDDIT_USERNAME and REDDIT_PASSWORD:
        return praw.Reddit(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            user_agent=USER_AGENT,
            username=REDDIT_USERNAME,
            password=REDDIT_PASSWORD,
        )
    return praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        user_agent=USER_AGENT,
    )

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clean(text: str) -> str:
    return " ".join(text.split())


def is_match_thread(title: str) -> bool:
    keywords = ["match thread", "post match", "pre-match", "post-match",
                 "half time", "half-time", "ft:", "ft |", "[ft]"]
    tl = title.lower()
    return any(k in tl for k in keywords)


# ---------------------------------------------------------------------------
# Collectors
# ---------------------------------------------------------------------------

def collect_posts(sub) -> list[dict]:
    """Pull from hot, top (week), top (month), controversial, new feeds."""
    feeds = [
        ("hot",           sub.hot(limit=POSTS_PER_FEED)),
        ("top_week",      sub.top("week",  limit=POSTS_PER_FEED)),
        ("top_month",     sub.top("month", limit=POSTS_PER_FEED)),
        ("controversial", sub.controversial("month", limit=POSTS_PER_FEED)),
        ("new",           sub.new(limit=POSTS_PER_FEED)),
    ]

    seen_ids = set()
    rows = []

    for feed_name, feed in feeds:
        print(f"  Fetching {feed_name}...")
        try:
            for post in feed:
                if post.id in seen_ids:
                    continue
                seen_ids.add(post.id)

                selftext = (post.selftext or "").strip()
                title    = (post.title    or "").strip()

                if selftext and selftext not in ("[deleted]", "[removed]"):
                    text = f"{title} — {selftext}"
                else:
                    text = title

                text = clean(text)
                if len(text) < MIN_TEXT_LEN:
                    continue

                rows.append({
                    "text":    text,
                    "label":   "",
                    "source":  "post",
                })
        except Exception as e:
            print(f"    Error in {feed_name}: {e}")

    print(f"  → {len(rows)} posts collected.")
    return rows


def collect_match_thread_comments(sub) -> list[dict]:
    """
    Pull top comments from match threads — the richest source of
    reaction-label examples in r/soccer.
    """
    rows = []
    print("\n  Scanning hot feed for match/post-match threads...")

    threads = []
    try:
        for post in sub.hot(limit=100):
            if is_match_thread(post.title):
                threads.append(post)
    except Exception as e:
        print(f"    Error fetching hot feed: {e}")
        return rows

    print(f"  → Found {len(threads)} match threads. Pulling comments...")

    for post in threads[:10]:   # cap at 10 threads
        print(f"    {post.title[:70]}")
        try:
            post.comment_sort = "top"
            post.comments.replace_more(limit=0)
            count = 0
            for comment in post.comments:
                body = clean(comment.body or "")
                if len(body) < MIN_TEXT_LEN or body in ("[deleted]", "[removed]"):
                    continue
                rows.append({
                    "text":   body,
                    "label":  "",
                    "source": "match_thread_comment",
                })
                count += 1
                if count >= COMMENTS_PER_THREAD:
                    break
        except Exception as e:
            print(f"    Error fetching comments: {e}")
        time.sleep(1)

    print(f"  → {len(rows)} match-thread comments collected.")
    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if "YOUR_CLIENT_ID" in CLIENT_ID:
        print("=" * 60)
        print("ERROR: You need to fill in your Reddit API credentials.")
        print()
        print("SETUP:")
        print("  1. Go to https://www.reddit.com/prefs/apps")
        print("  2. Click 'create another app'")
        print("  3. Name: anything | Type: script | Redirect URI: http://localhost:8080")
        print("  4. Click 'create app'")
        print("  5. Paste CLIENT_ID and CLIENT_SECRET into this script")
        print("     (or into a .env file and load with python-dotenv)")
        print("=" * 60)
        return

    print("=" * 60)
    print("TakeMeter — r/soccer data collector")
    print("=" * 60)

    reddit = build_reddit()
    sub    = reddit.subreddit(SUBREDDIT)

    print(f"\nConnected — collecting from r/{SUBREDDIT}\n")

    post_rows    = collect_posts(sub)
    comment_rows = collect_match_thread_comments(sub)

    all_rows = post_rows + comment_rows
    df = pd.DataFrame(all_rows, columns=["text", "label", "source"])
    df = df.drop_duplicates(subset="text").reset_index(drop=True)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    df.to_csv(OUT_PATH, index=False, quoting=csv.QUOTE_ALL)

    label_guide = {
        "post":                 "mostly hot_take / analysis — read carefully",
        "match_thread_comment": "almost always reaction — fast to label",
    }

    print(f"\n{'=' * 60}")
    print(f"Saved {len(df)} examples  →  {OUT_PATH}")
    print()
    print("Source breakdown:")
    for src, count in df["source"].value_counts().items():
        print(f"  {src:<30} {count:>4}   ({label_guide.get(src, '')})")
    print(f"{'=' * 60}")
    print()
    print("NEXT STEPS:")
    print("  1. Open data/rsoccer_raw.csv in Excel or VS Code")
    print("  2. Fill in the 'label' column for each row:")
    print("       analysis  — structured argument with specific evidence")
    print("       hot_take  — bold opinion asserted without evidence")
    print("       reaction  — emotional response to a specific event")
    print("  3. Aim for ≥200 labeled rows; target ~65-70 per label")
    print("  4. Save as data/rsoccer_labeled.csv when done")
    print()
    print("TIP: Sort by 'source' to batch your labeling — match thread")
    print("     comments are almost always 'reaction' and go fast.")


if __name__ == "__main__":
    main()
