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
- **Source:** r/soccer — top and hot posts and comments collected manually and via the Reddit public JSON API
- **Size:** 200+ labeled examples
- **Split:** 70% train / 15% validation / 15% test (stratified by label)

### Label Distribution
*(To be filled in after annotation is complete)*

| Label | Count | % |
|---|---|---|
| `analysis` | — | — |
| `hot_take` | — | — |
| `reaction` | — | — |

### Labeling Process
Each example was read and assigned exactly one label using the definitions and decision rules in `planning.md`. Posts that could not be cleanly assigned to any label (estimated <10%) were discarded rather than forced into a catch-all.

### Difficult Examples
*(Three genuinely hard-to-label examples and their decisions — to be filled in after annotation)*

1. **Example 1:** ...
2. **Example 2:** ...
3. **Example 3:** ...

---

## Model

- **Base model:** `distilbert-base-uncased` (HuggingFace)
- **Fine-tuning library:** Hugging Face `transformers` + `datasets`
- **Training compute:** Google Colab T4 GPU (~5–15 min)

### Key Hyperparameter Decisions
*(To be filled in after training)*

| Parameter | Value | Rationale |
|---|---|---|
| `num_train_epochs` | 3 | Standard starting point for small datasets; higher risks overfitting on 200 examples |
| `learning_rate` | 2e-5 | Standard for BERT-family fine-tuning |
| `per_device_train_batch_size` | 16 | Fits T4 GPU comfortably |

---

## Evaluation Results

*(To be filled in after running the notebook)*

### Overall Accuracy

| Model | Accuracy |
|---|---|
| Zero-shot baseline (Groq `llama-3.3-70b-versatile`) | — |
| Fine-tuned DistilBERT | — |

### Per-Class Metrics (Fine-Tuned Model)

*(Classification report to be pasted here)*

### Confusion Matrix

*(`confusion_matrix.png` to be added here)*

---

## Error Analysis

*(At least 3 wrong predictions with analysis — to be filled in after evaluation)*

### Wrong Prediction 1
...

### Wrong Prediction 2
...

### Wrong Prediction 3
...

### Reflection
*(What the model actually learned vs. what you intended it to learn)*

---

## Stretch Features

- [ ] Inter-annotator reliability (Cohen's kappa on 30 shared examples)
- [ ] Error pattern analysis (systematic grouping of failure modes)
- [ ] Deployed Gradio interface

---

## Repo Structure

```
ai201-project3-takemeter/
├── README.md                   # This file
├── planning.md                 # Label taxonomy, edge cases, milestone checklist
├── takemeter_starter.ipynb     # Colab fine-tuning + baseline notebook
├── data/
│   └── rsoccer_labeled.csv     # Annotated dataset (text, label columns)
├── evaluation_results.json     # Output from notebook — accuracy comparison
└── confusion_matrix.png        # Output from notebook — confusion matrix
```

---

## How to Run

1. Open `takemeter_starter.ipynb` in Google Colab
2. Set runtime to **T4 GPU** (Runtime → Change runtime type)
3. Add your Groq API key via Colab Secrets (key name: `GROQ_API_KEY`)
4. Upload `data/rsoccer_labeled.csv` when prompted
5. Run all cells — training takes ~5–15 minutes
6. Download `evaluation_results.json` and `confusion_matrix.png` and commit them here

---

## Requirements

No local install needed — the notebook runs entirely on Colab. For the Groq baseline, a free [Groq](https://console.groq.com/) account is required.
