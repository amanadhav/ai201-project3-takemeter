"""Pull extra posts from older time windows to supplement analysis examples."""
import requests, time, csv, pandas as pd

h = {"User-Agent": "takemeter/1.0"}
rows = []

windows = [
    (int(time.time()) - 365*86400, int(time.time()) - 270*86400),
    (int(time.time()) - 270*86400, int(time.time()) - 180*86400),
    (int(time.time()) - 540*86400, int(time.time()) - 365*86400),
]
for after, before in windows:
    r = requests.get("https://arctic-shift.photon-reddit.com/api/posts/search",
        params={"subreddit":"soccer","limit":100,"sort":"desc","after":after,"before":before},
        headers=h, timeout=20)
    if r.status_code == 200:
        data = r.json().get("data", [])
        added = 0
        for p in data:
            title = str(p.get("title","")).strip()
            selftext = str(p.get("selftext","")).strip()
            text = title + (" -- " + selftext if selftext and selftext not in ("[deleted]","[removed]") else "")
            if len(text) > 40:
                rows.append({"text": text, "label": "", "source": "post_older"})
                added += 1
        print("window", after, "->", added, "posts")
    time.sleep(1)

# High-engagement discussion comments from older posts
for after, before in windows[:2]:
    r2 = requests.get("https://arctic-shift.photon-reddit.com/api/posts/search",
        params={"subreddit":"soccer","limit":100,"sort":"desc","after":after,"before":before},
        headers=h, timeout=20)
    if r2.status_code != 200:
        continue
    posts = r2.json().get("data", [])
    mt_kw = ["match thread", "post match", "[ft]", "ft |", "starting xi"]
    discuss = [p for p in posts
               if int(p.get("num_comments", 0)) > 300
               and not any(k in p.get("title","").lower() for k in mt_kw)][:4]
    print("discussion posts:", len(discuss))
    for p in discuss:
        pid = p["id"]
        rc = requests.get("https://arctic-shift.photon-reddit.com/api/comments/search",
            params={"link_id": "t3_" + pid, "limit": 20, "sort": "desc"},
            headers=h, timeout=15)
        if rc.status_code == 200:
            for c in rc.json().get("data", []):
                body = str(c.get("body","")).strip()
                if len(body) > 100 and body not in ("[deleted]","[removed]"):
                    rows.append({"text": body, "label": "", "source": "discussion_comment_older"})
        time.sleep(0.5)

df = pd.DataFrame(rows).drop_duplicates(subset="text").reset_index(drop=True)
df.to_csv("data/rsoccer_extra.csv", index=False, quoting=csv.QUOTE_ALL)
print("Extra rows saved:", len(df))
