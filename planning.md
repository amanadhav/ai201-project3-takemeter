# TakeMeter — Planning Document
## AI201 · Project 3

---

## 1. Community

**Chosen community:** r/soccer (Reddit, ~3.5M members)

r/soccer is one of the largest English-language football communities online, covering global football at every level — World Cup, Champions League, Premier League, transfers, tactics, and fan culture. It was chosen because its discourse is genuinely *varied in quality and intent*: the same subreddit hosts detailed tactical breakdowns backed by xG data, one-line "X is overrated" assertions, and raw emotional reactions to goals in the same match thread. That range is exactly what makes it a strong domain for a discourse-quality classifier.

Crucially, the distinction between these modes of engagement *matters to community members*. r/soccer regulars will call out a "hot take without receipts" specifically, celebrate a well-reasoned breakdown, and distinguish reacting to a moment from actually arguing a position. The label taxonomy maps directly onto a social dynamic that already exists in the community.

A secondary reason for choosing r/soccer is that posts span multiple registers — short one-liners, long tactical essays, live match comments, and transfer news — which ensures that the model has to learn something real, not just length-based classification.

---

## 2. Labels

### `analysis`
**Definition:** The post makes a structured argument supported by specific, verifiable evidence — statistics, tactical observations with named formations or roles, historical comparisons, or multi-season data. The reasoning is explicit: a claim is stated and the evidence offered is sufficient to falsify or support it even after the opinion framing is removed.

**Example 1 (clear):**
> "City's high line is why they're conceding so many headers this season — opponents are winning 68% of aerial duels in the final third against them, up from 54% last year. Pep hasn't adjusted and it's costing them points."

**Example 2 (clear):**
> "A list of all players who have been top-assister of a league season tracked by fbref.com at least 3 times. Dusan Tadic: 7 times (10/11 NED, 13/14 NED, 19/20 NED…). De Bruyne: 6 times. Messi: 6 times."

---

### `hot_take`
**Definition:** A bold, confident opinion stated without meaningful supporting evidence. The post asserts a position rather than argues one. The claim may use a vague supporting phrase or a single cherry-picked stat for rhetorical effect, but the reasoning chain is absent — the reader is expected to react to the claim, not evaluate evidence.

**Example 1 (clear):**
> "The current Real Madrid team might be underrated."

**Example 2 (clear):**
> "Is Ronaldo's hattrick vs Spain in 2018 the greatest ever??? Genuinely think no other player pulls that off in that moment."

---

### `reaction`
**Definition:** An immediate emotional response to a specific, recent event — a goal, final score, red card, transfer announcement, retirement, fan moment, or match incident. The post expresses a feeling about something that just happened; there is minimal to no structured argument, and the post's primary function is emoting rather than reasoning.

**Example 1 (clear):**
> "THAT BELLINGHAM HEADER. WHAT A PLAYER OH MY GOD" *(match thread comment after a goal)*

**Example 2 (clear):**
> "Brazil 1-1 Morocco at MetLife felt like watching the 2022 quarterfinal collapse start one round early" *(immediate post-match reaction)*

---

## 3. Hard Edge Cases

### Edge Case 1: News / Announcement Posts
**What it looks like:** "[Fabrizio Romano] Andrés Iniesta set to start his managerial career, all agreed."
**Problem:** It's not analysis (no argument), not a hot take (no opinion), not a reaction (no emotion). It's a factual report.
**Decision rule:** Pure news and transfer announcements that contain no opinion, argument, or emotional framing are **excluded from the dataset** entirely. If a post reports news AND immediately editorializes on it (e.g., "Iniesta takes coaching job — this is a disaster waiting to happen"), the editorial clause makes it labelable as `hot_take`.

### Edge Case 2: Pundit Quotes That Make Claims
**What it looks like:** "Micah Richards: 'Madrid winning the UCL? Right now I'd say no. Barcelona and Bayern are better. But Madrid have players for the biggest moments.'"
**Problem:** It's an opinion (hot take framing) but it's also a reported quote with some reasoning.
**Decision rule:** If the quote contains reasoning (even brief), label `hot_take`. If it cites stats, label `analysis`. The key question is: does the post author or the quoted person provide verifiable evidence? A pundit saying "Madrid have players for big moments" — without data — is `hot_take`. A pundit saying "their conversion rate in knockout games is 73%" would be `analysis`.

### Edge Case 3: Historical Stat Posts Triggered by a Match
**What it looks like:** "Across the entirety of the 2018 and 2022 World Cups, there were 4 games won by 4+ goals. At 2026, there have already been 6."
**Problem:** It's a statistical post (could be `analysis`) but it's triggered by a specific event and expresses surprise (could be `reaction`).
**Decision rule:** If the primary content is a presented data comparison with a clear point being made about a trend, label `analysis`. If the stat is a single factoid used to express amazement or contrast (without a broader argument), label `reaction`. The tiebreaker: would this post make sense as a standalone analytical observation if you removed the World Cup context? If yes → `analysis`. If it only makes sense as a live reaction → `reaction`.

### Edge Case 4: Short Match Thread Comments That Also Argue
**What it looks like:** "I know Madrid fans ain't happy Spain won and are waiting on their downfall."
**Problem:** It's a match thread comment (reaction context) but also contains an opinion about fan behavior.
**Decision rule:** Match thread comments are labeled `reaction` by default unless the comment contains a structured argument with at least two connected logical claims. A single sentence that combines an emotional stance with an opinion is still `reaction`.

---

## 4. Data Collection Plan

**Source:** r/soccer via the Arctic Shift API (open Reddit archive, no authentication required). The collection script (`data/collect_rsoccer.py`) pulls from four time windows (last 7 days, 7–30 days, 30–90 days, 90–180 days) to capture both World Cup reaction content and longer-form discussion posts, plus match thread comments for reaction-label coverage.

**Raw collected:** 343 examples (308 post titles + selftext, 35 match thread comments).

**Exclusions:** Posts are excluded if they are (a) pure news/transfer announcements with no editorial content, (b) match thread body posts containing full lineups and play-by-play (not classifiable), or (c) commercial posts (ticket sales, merchandise).

**Target per label:** 65–75 examples each for `analysis`, `hot_take`, and `reaction` (total 195–225 labeled examples).

**Imbalance contingency:** After an initial labeling pass, if any label is below 50 examples, additional examples will be collected by:
- For underrepresented `analysis`: searching r/soccer for self-posts (text posts) with high comment counts, which tend to be tactical threads.
- For underrepresented `hot_take`: browsing r/soccer's controversial sort, which surfaces debated opinion posts.
- For underrepresented `reaction`: pulling more match thread comments from specific high-profile matches.

**Pre-labeling approach:** A heuristic Python script (`data/prelabel.py`) was used to assign initial labels to all 343 examples based on structural features (source type, text length, keyword patterns, formatting). Every pre-assigned label was reviewed and corrected manually before the final `rsoccer_labeled.csv` was saved. This is documented as AI assistance in the AI Tool Plan section.

---

## 5. Evaluation Metrics

**Primary metric: Per-class F1 score** (harmonic mean of precision and recall for each label).

Accuracy alone is insufficient here for two reasons. First, even with a roughly balanced dataset (~33% per class), a model that learns to always predict the majority class would achieve ~33–40% accuracy — high enough to look acceptable without having learned anything. Second, the failure modes for each label have different costs:

- Missing `analysis` posts (high recall priority): the community tool's main value is flagging substantive posts. False negatives on `analysis` mean the tool fails its core purpose.
- False positives on `hot_take` (high precision priority): mislabeling a good analytical post as a hot take is the most reputationally damaging error for users.

**Secondary metrics:**
- **Macro F1** (unweighted average across classes): treats all three classes equally, appropriate given balanced label distribution.
- **Confusion matrix**: reveals which specific label pairs the model confuses, e.g., whether it conflates `analysis` and `hot_take` or `reaction` and `hot_take`.
- **Per-class precision and recall**: separately reported to diagnose asymmetric errors.

**Baseline comparison:** The Groq zero-shot baseline (`llama-3.3-70b-versatile`) is evaluated on the same test set under the same metrics. The fine-tuned model must outperform the baseline on macro F1 to justify the annotation effort.

---

## 6. Definition of Success

A classifier is "genuinely useful" for a real r/soccer community tool if it can reliably distinguish between content types that community members themselves recognize as qualitatively different. Based on that, the specific thresholds are:

| Metric | Minimum threshold | Target |
|---|---|---|
| Fine-tuned model accuracy | > 70% | > 80% |
| Per-class F1 (each label) | > 0.60 | > 0.70 |
| Macro F1 | > 0.65 | > 0.75 |
| Improvement over baseline | > +5pp accuracy | > +10pp accuracy |

**"Good enough for deployment"** means: macro F1 ≥ 0.70, with no individual class F1 below 0.60. A classifier that works well on two of three labels but completely fails on one is not deployable — it would systematically mislead users on that label.

**Ceiling check:** If the fine-tuned model exceeds 95% accuracy on this task, that would be suspicious. The labels involve genuine subjectivity (a pundit quote with one stat is legitimately borderline between `hot_take` and `analysis`). Suspiciously high accuracy likely indicates test set contamination or labels that are too easy (e.g., length-based) rather than true content understanding.

---

## AI Tool Plan

### Label Stress-Testing
Before finalizing annotation, the Cursor AI assistant was asked to generate 5 boundary-case posts — posts designed to be genuinely ambiguous between two labels. The stress-test examples produced, and the decision rules they forced:

1. **`analysis` vs `hot_take`**: "Mbappe is overrated — his playoff win rate against top-seeded opponents is below .500." → Cherry-picked stat with dismissive framing → `hot_take`. Decision rule: a single stat used to support a dismissive label without explaining a mechanism is still `hot_take`.

2. **`reaction` vs `hot_take`**: "If Arsenal lose this they deserve to be out of the title race — their squad depth has been exposed all season." → Triggered by event but makes a structural claim. Post length and detail level determine: one-sentence claim → `hot_take` (the "squad depth" assertion isn't backed up here); multi-paragraph breakdown → `analysis`.

3. **`reaction` vs `analysis`**: "Germany's 7-1 in the first round means they've already matched the total number of big-margin wins from the entire 2018 and 2022 World Cups combined." → Single factoid to express amazement → `reaction`. If followed by analysis of why Germany scores in bunches → `analysis`.

4. **`hot_take` vs `analysis`**: "Rodri is the best DM in the world — his progressive pass completion under pressure is 91%." → One stat with superlative framing → the stat is specific and verifiable, which moves it toward `analysis`. But if the post only cites that one number without making a reasoning chain, it stays `hot_take`.

5. **`reaction` vs `hot_take`**: "Ferran is such a bum — how does he keep getting called up?" → Emotional, derogatory, event-triggered (watching a match) → `reaction` (expressly emotional about a player in a specific game context, not a considered opinion).

These five examples are genuine hard cases. They sharpened the decision rules in Section 3 above.

### Annotation Assistance
A heuristic Python script (`data/prelabel.py`) was developed with the Cursor AI assistant to pre-label all 343 raw examples before manual review. The script uses structural features — source type, text length, keyword patterns (e.g., score update format, analysis vocabulary, opinion markers) — to assign initial labels. Every pre-assigned label was subsequently reviewed by the project author, with corrections documented in `data/rsoccer_labeled.csv` via the `notes` column.

**Disclosure:** The `notes` column in the CSV indicates "pre-labeled" for rows that received an initial AI-assisted label and "reviewed" for rows where the assigned label was confirmed or changed after manual inspection. This workflow is consistent with Milestone 3 guidance, which permits pre-labeling provided every label is reviewed individually.

### Failure Analysis
After running the notebook and obtaining wrong predictions, the plan is to:
1. Export the wrong predictions (text, true label, predicted label, confidence) to a structured prompt
2. Feed that prompt to a Groq LLM or Cursor AI asking: "What patterns do you see across these errors? Are there shared linguistic features — length, specific vocabulary, hedging language — that might explain why the model confused these pairs?"
3. The AI-suggested patterns will be verified by manually counting examples in each proposed pattern category before writing the evaluation report
4. The final error analysis in the README will cite only patterns that appear in at least 3 wrong predictions and can be described with a falsifiable characterization (e.g., "short posts under 50 characters are consistently misclassified as `reaction` regardless of content")

---

## Milestone Checklist

- [x] Community chosen: r/soccer
- [x] Labels defined with one-sentence definitions
- [x] 2 clear examples per label
- [x] Hard edge cases documented with decision rules
- [x] Data collection plan written (Arctic Shift API)
- [x] Evaluation metrics defined with justification
- [x] Success criteria with specific numeric thresholds
- [x] AI Tool Plan: label stress-testing complete
- [x] AI Tool Plan: annotation assistance approach documented
- [x] AI Tool Plan: failure analysis plan documented
- [x] 200+ examples collected and labeled (239 total)
- [x] Label distribution verified (33/33/33% — no label above 70%)
- [x] Fine-tuning pipeline run (DistilBERT, 3 epochs, T4 GPU)
- [x] Groq baseline run (llama-3.3-70b-versatile, zero-shot)
- [x] Evaluation report written (see README)
