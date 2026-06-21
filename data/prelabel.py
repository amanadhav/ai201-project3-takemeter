"""
prelabel.py
-----------
Heuristic pre-labeler for rsoccer_raw.csv.
Assigns an initial label (analysis / hot_take / reaction / skip) to each
post based on structural features, then saves the result for manual review.

This is AI-assisted pre-labeling as described in planning.md.
Every label must be reviewed and corrected before the final
rsoccer_labeled.csv is used for training.

Usage:
    python data/prelabel.py

Output:
    data/rsoccer_labeled.csv  — pre-labeled, with a 'notes' column
                                showing the rule that fired
"""

import re
import csv
import pandas as pd
from pathlib import Path

IN_PATH  = Path(__file__).parent / "rsoccer_raw.csv"
OUT_PATH = Path(__file__).parent / "rsoccer_labeled.csv"

# ---------------------------------------------------------------------------
# Rule-based labeler
# ---------------------------------------------------------------------------

def label(text: str, source: str) -> tuple[str, str]:
    """
    Returns (label, rule_note) where label is one of:
        analysis | hot_take | reaction | skip
    """
    t   = str(text).strip()
    tl  = t.lower()
    tln = len(t)

    # -----------------------------------------------------------------------
    # SKIP — not classifiable by taxonomy
    # -----------------------------------------------------------------------

    # Match thread body posts: very long with structural markers
    if tln > 1500 and any(k in tl for k in
            ["auto-refreshing", "line-ups", "starting xi", "match events | via espn",
             "subs:", "substitution, ", "corner. assisted by"]):
        return "skip", "match_thread_body"

    # Post match thread body (contains full match stats table)
    if tln > 1000 and "match stats" in tl and "possession" in tl and "shots on goal" in tl:
        return "skip", "post_match_thread_body"

    # Pure news/transfer sourced posts — short, bracketed source, no opinion
    news_source = re.match(r'^\[.{1,60}\]\s', t)
    has_opinion = re.search(
        r'(overrated|underrated|should|best|worst|hate|love|better|terrible'
        r'|fire him|sack him|disgrace|brilliant|awful|amazing|pathetic)',
        tl
    )
    if news_source and tln < 300 and not has_opinion:
        return "skip", "news_post"

    # Ticket/commercial/off-topic posts
    if any(k in tl for k in ["tickets available", "for sale", "ebay", "promo code",
                              "affiliate", "pixel cleaning"]):
        return "skip", "commercial"

    # Match thread schedule / preview boilerplate
    if re.match(r'^match thread:', t, re.IGNORECASE) and tln < 300:
        return "skip", "match_thread_header"

    # Very long manager preview posts (not r/soccer community takes)
    if tln > 5000:
        return "skip", "too_long_article"

    # What to watch this week schedule posts
    if "what to watch this week" in tl and tln > 500:
        return "skip", "schedule_post"

    # -----------------------------------------------------------------------
    # REACTION — immediate emotional response to specific event
    # -----------------------------------------------------------------------

    # Match thread comments are almost always reactions
    if source == "match_thread_comment":
        return "reaction", "match_thread_comment"

    # Goal / score update posts: "[N]-N" pattern + short
    score_update = re.search(r'(?<!\w)\[\d+\][\s\-–]+\d+', t)
    if score_update and tln < 180:
        return "reaction", "score_update"

    # Short result-line posts: "Germany 7-1 Curacao" style
    result_line = re.match(r'^[\w\s\[\]()]+\d[\-–]\d[\w\s]+$', t.split('--')[0].strip())
    if result_line and tln < 150:
        return "reaction", "result_line"

    # "X becomes / scored / makes history" first-ever posts (event-tied factoid)
    if re.search(r'(becomes|scored|makes history|first (player|team|country|time)|'
                 r'only (player|team)|sets|breaks|equalled)', tl) \
            and tln < 350 \
            and not re.search(r'(xg|possession|pass completion|per 90|tactical)', tl):
        return "reaction", "historic_moment_factoid"

    # Fan celebration / tribute posts
    if any(k in tl for k in ["fans celebrating", "fans before", "comforting after",
                              "show love", "tribute", "farewell", "retirement",
                              "retired from the beautiful game"]) and tln < 600:
        return "reaction", "fan_moment"

    # Seeing / watching posts — personal live reaction
    if re.match(r'^(seeing|watching|just saw|witnessing)', tl) and tln < 300:
        return "reaction", "personal_reaction"

    # Very short celebratory / shocked posts
    if tln < 80 and re.search(r'(what a|oh my|holy|lmao|wtf|lol|incredible|unreal'
                                r'|this is insane|can t believe)', tl):
        return "reaction", "short_exclamation"

    # -----------------------------------------------------------------------
    # ANALYSIS — structured argument with specific evidence
    # -----------------------------------------------------------------------

    # Long posts with analytical vocabulary
    analytical_kw = [
        "xg", "expected goals", "possession %", "pressing intensity",
        "progressive passes", "formation", "high line", "tactical",
        "per 90", "pass completion", "win rate", "underlying numbers",
        "statistically", "since records began", "all-time", "historically",
        "according to", "data shows", "coefficient", "financial fair play",
        "transfer fee record", "inflation adjusted",
    ]
    analytical_hits = sum(1 for k in analytical_kw if k in tl)
    if tln > 350 and analytical_hits >= 1:
        return "analysis", "long_analytical"

    # Long posts with tables or structured lists (multi-season stats)
    has_table = ("---" in t and t.count("|") > 4) or t.count("\n") > 6
    if tln > 500 and has_table and any(k in tl for k in
            ["season", "goals", "assists", "league", "world cup", "top scorer"]):
        return "analysis", "statistical_table"

    # Very long self-posts that aren't news (explainers, deep dives)
    is_news_ish = bool(news_source) or any(k in tl[:100] for k in
        ["official", "confirmed", "signing", "transfer", "appointed"])
    if tln > 1000 and not is_news_ish:
        return "analysis", "long_form_post"

    # Medium-length posts with multiple data points or years cited
    years_mentioned = len(re.findall(r'\b(19|20)\d\d\b', t))
    if tln > 400 and years_mentioned >= 3:
        return "analysis", "multi_season_comparison"

    # -----------------------------------------------------------------------
    # HOT TAKE — bold opinion without supporting evidence
    # -----------------------------------------------------------------------

    # Classic opinion markers
    hot_take_patterns = [
        r'\bis\b.{0,30}\b(overrated|underrated|the best|the worst|elite|trash|a bum)\b',
        r'\bwill never\b',
        r'\b(should|deserves? to) (be|have|win|get)\b',
        r'^(honestly|actually|unpopular opinion|hot take|controversial take)',
        r'\b(change my mind|fight me|prove me wrong)\b',
        r'\b(can we please|why (is|does|did|are|can)|how (is|does|can))\b',
        r'\b(am i the only one|does anyone else|seriously though)\b',
        r'\bthe greatest\b.{0,30}\bever\b',
        r'\b(fire|sack) (him|the|our)\b',
    ]
    if any(re.search(p, tl) for p in hot_take_patterns):
        return "hot_take", "opinion_marker"

    # Hard opinion keywords
    hot_take_kw = [
        "overrated", "underrated", "bum", "trash", "goat", "greatest ever",
        "best ever", "worst ever", "most overrated", "genuinely think",
        "unpopular", "controversy", "hot take", "i mean come on",
        "genuinely believe", "couldn't even", "has no business",
        "got their asses kicked", "shameful", "disgusting", "braindead",
    ]
    if any(k in tl for k in hot_take_kw):
        return "hot_take", "opinion_keyword"

    # Questions asserting a position (not just asking for information)
    if t.rstrip().endswith("?") and tln < 250:
        opinionated = re.search(
            r'\b(best|worst|greatest|better|should|could|would|overrated'
            r'|underrated|deserve|ever|most|more)\b', tl
        )
        if opinionated:
            return "hot_take", "opinionated_question"

    # Short pundit/player quotes making bold claims
    is_quote = bool(re.match(r'^[\w\s\[\]]+:\s*"', t)) or t.startswith('"')
    if is_quote and tln < 500:
        bold_claim = re.search(
            r'\b(better|best|worst|never|always|should|must|think|believe'
            r'|right now|the problem|the issue|doesn.t deserve)\b', tl
        )
        if bold_claim:
            return "hot_take", "pundit_quote_opinion"

    # -----------------------------------------------------------------------
    # Default fallbacks — ordered from most to least specific
    # -----------------------------------------------------------------------

    # Any post making a judgment, comparison, or quality assertion → hot_take
    # even if triggered by a specific event
    judgment_words = [
        r'\b(is|was|were|are)\b.{0,40}\b(good|bad|poor|great|terrible|awful|brilliant'
        r'|embarrassing|shameful|pathetic|incredible|class|clinical|dominant)\b',
        r'\b(better|worse|best|worst)\s+than\b',
        r'\b(deserves?|should|has to|needs to|must)\b',
        r'\b(letting|allowing|conceding).{0,30}\b(embarrassing|bad|poor|should)',
        r'\b(not|never|no way|can.t believe)\b.{0,30}\b(win|beat|score|compete)\b',
        r'\b(as good as|as bad as|same as|comparable to)\b',
        r'\bproves?\b.{0,40}\b(point|right|wrong|theory)\b',
        r'^(i|we) (stop|stopped|hate|love|can.t)',
    ]
    if any(re.search(p, tl) for p in judgment_words):
        return "hot_take", "judgment_assertion"

    # First-person opinion posts
    if re.search(r'^(i |we |my |honestly |actually |tbh |imo |in my )', tl) and tln < 400:
        return "hot_take", "first_person_opinion"

    # Questions that invite debate even without opinionated keywords
    if t.rstrip().endswith("?") and tln < 300:
        return "hot_take", "discussion_question"

    # Short unclassified posts that aren't clearly emotive → hot_take
    # (short posts in r/soccer are usually quick takes, not neutral reporting)
    if tln < 120:
        is_purely_emotive = re.search(
            r'^(what a|oh my|holy|lmao|wtf|lol|incredible|unreal'
            r'|this is|look at|just saw|haha)', tl
        )
        if is_purely_emotive:
            return "reaction", "short_exclamation"
        return "hot_take", "short_opinion"

    # Medium posts with soft opinion language
    if tln < 400 and re.search(
        r'\b(i think|i believe|honestly|actually|feel like|seems like|looks like'
        r'|clearly|obviously|definitely|absolutely)\b', tl
    ):
        return "hot_take", "soft_opinion"

    # Remaining short posts
    if tln < 200:
        return "reaction", "short_default"

    # Longer unclassified posts → analysis (substantive enough to have an argument)
    return "analysis", "long_default"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    df = pd.read_csv(IN_PATH)
    print(f"Loaded {len(df)} rows from {IN_PATH.name}")

    labels, notes = [], []
    for _, row in df.iterrows():
        lbl, note = label(row["text"], row.get("source", "post"))
        labels.append(lbl)
        notes.append(note)

    df["label"] = labels
    df["notes"] = notes

    # --- Stats before filtering ---
    print("\nRaw distribution (including skips):")
    print(df["label"].value_counts().to_string())

    # --- Keep only labelable rows ---
    keep = df[df["label"] != "skip"].copy()

    # --- Balance: cap each label at 80 to stay balanced ---
    # After manual review the user can trim or add more examples.
    parts = [g.sample(min(len(g), 80), random_state=42) for _, g in keep.groupby("label")]
    per_label = pd.concat(parts).reset_index(drop=True)

    # Shuffle so label ordering isn't visible during annotation
    per_label = per_label.sample(frac=1, random_state=42).reset_index(drop=True)

    print(f"\nAfter skip removal and cap (80 per label):")
    print(per_label["label"].value_counts().to_string())
    print(f"Total: {len(per_label)}")

    # Save with notes so the reviewer can understand each pre-assigned label
    per_label[["text", "label", "source", "notes"]].to_csv(
        OUT_PATH, index=False, quoting=csv.QUOTE_ALL
    )

    print(f"\nSaved -> {OUT_PATH.name}")
    print()
    print("REVIEW INSTRUCTIONS:")
    print("  Open rsoccer_labeled.csv. For each row:")
    print("  1. Read the 'text' column")
    print("  2. Check the pre-assigned 'label' — correct it if wrong")
    print("  3. Aim for at least 200 rows with ~65-70 per label")
    print("  4. The 'notes' column explains the rule that fired — useful for review")
    print("  5. Delete 'source' and 'notes' columns when done")
    print("     (notebook only needs 'text' and 'label')")


if __name__ == "__main__":
    main()
