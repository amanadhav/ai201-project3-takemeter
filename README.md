# TakeMeter — r/soccer Discourse Classifier
**AI201 · Project 3**

A fine-tuned text classifier that evaluates the quality and type of discourse in r/soccer posts. Given a Reddit post or comment, the model predicts whether it is analytical reasoning, a hot take, or an emotional reaction.

---

## Community

**r/soccer** (~3.5M members) — one of the largest global football communities on Reddit. Discourse ranges from detailed tactical analysis to fiery one-liners and live match reactions. The distinction between a reasoned argument and a confident assertion is real and recognized by regulars in the community, making it a strong domain for discourse quality classification.

---

## Label Taxonomy

| Label | Definition |
|---|---|
| `analysis` | Structured argument backed by specific, verifiable evidence — statistics, tactical breakdowns, or historical comparisons. The reasoning is explicit. |
| `hot_take` | Bold, confident opinion stated without meaningful supporting evidence. Asserts rather than argues. May use one decorative stat but lacks a reasoning chain. |
| `reaction` | Immediate emotional response to a specific event (goal, result, transfer, red card). Expresses a feeling with little to no structured argument. |

See [`planning.md`](./planning.md) for full definitions, two clear examples per label, one uncertain example per label, and the decision rules used to handle edge cases.

---

## Dataset

### Collection
- **Source:** r/soccer via the [Arctic Shift API](https://arctic-shift.photon-reddit.com) — open Reddit archive, no authentication required
- **Collection script:** `data/collect_rsoccer.py` — pulls across multiple time windows (7 days to 18 months ago) for variety; also collects match thread comments as a targeted source of `reaction` examples
- **Size:** 239 labeled examples
- **Split:** 70% train / 15% validation / 15% test (stratified by label, handled automatically by the notebook)

### Label Distribution

| Label | Count | % |
|---|---|---|
| `analysis` | 79 | 33.1% |
| `hot_take` | 80 | 33.5% |
| `reaction` | 80 | 33.5% |

### Labeling Process
Data was collected via the Arctic Shift API, then pre-labeled using a heuristic Python script (`data/prelabel.py`) that assigns initial labels based on source type, text length, keyword patterns (e.g., score update format, analytical vocabulary, opinion markers), and structural features. Every pre-assigned label was reviewed manually. Posts that could not be cleanly assigned to any label (~15% of collected data) were discarded.

**AI assistance disclosure:** The pre-labeling heuristics were developed with AI assistance. The `notes` column in `data/rsoccer_labeled.csv` records which rule fired for each row, enabling transparent review of every AI-assisted label.

### Difficult Examples

**1. Stat post triggered by a match:**
> "Across the entirety of the 2018 and 2022 World Cups, there were 4 games won by 4+ goals. At 2026, there have already been 6."

This cites a specific comparison (could be `analysis`) but is clearly triggered by a live World Cup event and expresses amazement rather than making an argument. **Decided: `reaction`** — the stat is a single factoid used to express surprise, not a reasoning chain. Decision rule: a standalone stat that emphasizes magnitude of an event without arguing a broader point is `reaction`.

**2. Pundit quote with one embedded stat:**
> "Arne Slot on Arsenal winning the PL: 'First time in 30 years that a team had 40% of their goals from set-pieces.'"

The quote cites a specific verifiable stat (could be `analysis`) but is a pundit offering a one-sentence observation, not a structured argument. **Decided: `hot_take`** — a reported opinion that includes a single stat for rhetorical effect without a reasoning chain stays `hot_take`.

**3. Match thread comment making a structural claim:**
> "I know Madrid fans ain't happy Spain won and are waiting on their downfall."

Posted in a match thread (reaction context) but makes an assertion about fan behavior that isn't purely emotional. **Decided: `reaction`** — the claim is throwaway justification attached to an emotional in-game comment, not a considered argument.

---

## Model

- **Base model:** `distilbert-base-uncased` (HuggingFace)
- **Fine-tuning library:** Hugging Face `transformers` + `datasets`
- **Training compute:** Google Colab T4 GPU (~10 minutes)

### Key Hyperparameter Decisions

| Parameter | Value | Rationale |
|---|---|---|
| `num_train_epochs` | 3 | Standard starting point for small datasets; more epochs risk overfitting on ~167 training examples |
| `learning_rate` | 2e-5 | Standard for BERT-family fine-tuning; lower values are more stable on small datasets |
| `per_device_train_batch_size` | 16 | Fits T4 GPU comfortably without OOM errors |
| `warmup_steps` | 50 | Prevents large gradient updates in early training on a small dataset |

No hyperparameters were changed from the notebook defaults — the 3-epoch/2e-5 configuration is well-established for DistilBERT on datasets of this size.

---

## Evaluation Results

### Overall Accuracy

| Model | Accuracy | Test Set Size |
|---|---|---|
| Zero-shot baseline (Groq `llama-3.3-70b-versatile`) | **38.9%** | 36 |
| Fine-tuned DistilBERT | **69.4%** | 36 |
| **Improvement** | **+30.6pp** | — |

Random chance on a balanced 3-class task = 33.3%. The baseline (38.9%) barely exceeded random, indicating this task is genuinely hard for a general-purpose LLM with no training signal. Fine-tuning produced a +30.6 percentage point improvement.

### Per-Class Metrics (Fine-Tuned Model)

Derived from the confusion matrix below (test set = 36 examples, 12 per class):

| Label | Precision | Recall | F1 |
|---|---|---|---|
| `analysis` | 0.71 | **1.00** | **0.83** |
| `hot_take` | 0.62 | 0.67 | 0.64 |
| `reaction` | **0.83** | 0.42 | 0.56 |
| **Macro avg** | **0.72** | **0.70** | **0.68** |

### Confusion Matrix

```
                 Predicted
                 analysis  hot_take  reaction
True  analysis  [  12        0         0   ]
      hot_take  [   3        8         1   ]
      reaction  [   2        5         5   ]
```

![Confusion Matrix](confusion_matrix.png)

**Reading the matrix:**
- `analysis` was identified perfectly — 12/12 correct, 0 missed
- `hot_take` had moderate performance — 8/12 correct; 3 misclassified as `analysis`, 1 as `reaction`
- `reaction` was the weakest — 5/12 correct; 5 misclassified as `hot_take`, 2 as `analysis`

---

## Error Analysis

### Wrong Prediction 1 — `reaction` predicted as `hot_take`

The most common error (5 cases). Reaction posts that contain opinion language about a player or team during a live match get classified as `hot_take`. For example, a match thread comment like *"Ferran is such a bum — how does he keep getting called up?"* was labeled `reaction` (it's an in-the-moment complaint while watching Spain play) but has the surface form of a `hot_take` (criticism of a player without evidence). The model has no access to the match thread context — it only sees the text — so opinion vocabulary dominates.

### Wrong Prediction 2 — `hot_take` predicted as `analysis`

Three cases where a `hot_take` was over-classified as `analysis`. These were typically pundit quotes or posts containing one specific stat embedded in an otherwise assertive opinion. For example, a post citing "40% of Arsenal's goals came from set-pieces this season" as part of a broader pundit statement was labeled `hot_take` (single stat, no reasoning chain) but the presence of a specific percentage may have triggered the model's `analysis` pattern. The model appears to weight the presence of numbers heavily regardless of whether they form a genuine argument.

### Wrong Prediction 3 — `reaction` predicted as `analysis`

Two cases where longer reaction posts were misclassified as `analysis`. These were posts like "Germany's 7-1 means they've already matched the total big-margin wins from the entire 2018 and 2022 World Cups combined" — labeled `reaction` (single factoid expressing amazement at a live event) but the multi-tournament comparison triggered the model's `analysis` pattern. The model seems to have learned that cross-tournament comparisons signal `analysis` regardless of whether an argument is being made.

### Reflection: What the Model Learned vs. What Was Intended

**What was intended:** Distinguish posts by their *reasoning process* — does this post offer falsifiable evidence that supports a claim?

**What the model actually learned:** Distinguish posts largely by *surface features* — long structured text with numbers → `analysis`; short opinion vocabulary (overrated, bum, elite) → `hot_take`; match thread source and very short exclamatory text → `reaction`.

This explains the specific failure pattern. The `reaction`/`hot_take` boundary in particular depends on *context* (was this written during a live match? is this an unprompted opinion vs. an in-game reaction?) which is not available in the raw text alone. The model learned a reasonable proxy — `hot_take` language tends to be more deliberate and `reaction` language more exclamatory — but it fails when a live match comment happens to use assertive language.

`analysis` was learned nearly perfectly because it has the strongest surface signal: long text, specific numbers, multi-sentence reasoning chains, tabular structure. The model didn't need to understand the reasoning — it just needed to recognize what analytical posts *look like*.

---

## Against Success Criteria

| Metric | Target | Achieved | Met? |
|---|---|---|---|
| Fine-tuned accuracy | > 70% | 69.4% | Borderline |
| Per-class F1 (each label) | > 0.60 | 0.83 / 0.64 / 0.56 | Partial (`reaction` below threshold) |
| Macro F1 | > 0.65 | 0.68 | Yes |
| Improvement over baseline | > +5pp | +30.6pp | Yes |

The model meets the macro F1 threshold and substantially exceeds the baseline improvement target. The `reaction` class F1 (0.56) falls below the per-class threshold of 0.60, driven by low recall — the model only catches 5 of 12 true reaction examples. This is the primary failure mode and is partly attributable to the inherent ambiguity between `reaction` and `hot_take` when match-thread context is unavailable.

---

## Stretch Features

- [ ] Inter-annotator reliability (Cohen's kappa on 30 shared examples)
- [ ] Error pattern analysis (systematic grouping of failure modes)
- [ ] Deployed Gradio interface

---

## Repo Structure

```
ai201-project3-takemeter/
├── README.md                        # This file — full evaluation report
├── planning.md                      # Label taxonomy, edge cases, AI tool plan
├── takemeter_starter.ipynb          # Colab fine-tuning + baseline notebook
├── evaluation_results.json          # Accuracy comparison (baseline vs fine-tuned)
├── confusion_matrix.png             # Fine-tuned model confusion matrix (test set)
└── data/
    ├── collect_rsoccer.py           # Arctic Shift API data collection script
    ├── prelabel.py                  # AI-assisted heuristic pre-labeler
    ├── rsoccer_labeled.csv          # Full annotated dataset (text, label, notes)
    ├── rsoccer_labeled_clean.csv    # Notebook-ready CSV (text + label only)
    ├── rsoccer_raw.csv              # Raw collected data (unlabeled)
    └── rsoccer_extra.csv            # Supplementary collection (older time windows)
```

---

## How to Run

1. Open `takemeter_starter.ipynb` in Google Colab
2. Set runtime to **T4 GPU** (Runtime → Change runtime type)
3. Add your Groq API key via Colab Secrets (key name: `GROQ_API_KEY`)
4. Upload `data/rsoccer_labeled_clean.csv` when prompted in Section 1
5. Run all cells in order — training takes ~10 minutes
6. Download `evaluation_results.json` and `confusion_matrix.png` from the Files panel

---

## Requirements

No local install needed — the notebook runs entirely on Google Colab (free tier). For the Groq zero-shot baseline, a free [Groq](https://console.groq.com/) account is required.
