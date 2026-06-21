"""
demo.py — TakeMeter Gradio Interface
-------------------------------------
Loads the fine-tuned DistilBERT model and serves a local web UI for
classifying r/soccer posts as analysis / hot_take / reaction.

SETUP:
  1. In Colab, after training, download the model folder:
       Files panel → right-click 'takemeter-model' → Download
     This downloads a zip. Extract it so the folder structure is:
       takemeter-model/
         config.json
         model.safetensors   (or pytorch_model.bin)
         tokenizer_config.json
         ...
  2. Place the 'takemeter-model' folder in the same directory as this file.
  3. Run:
       pip install transformers gradio torch
       python demo.py
  4. Open http://localhost:7860 in your browser.

Alternatively, run Section 7 of takemeter_starter.ipynb in Colab for an
in-notebook version that requires no local download.
"""

from pathlib import Path
import torch
import torch.nn.functional as F
import gradio as gr
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# ---------------------------------------------------------------------------
# Load model
# ---------------------------------------------------------------------------

MODEL_PATH = Path(__file__).parent / "takemeter-model"

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Model not found at {MODEL_PATH}.\n"
        "Download the 'takemeter-model' folder from Colab and place it here.\n"
        "See the docstring at the top of this file for instructions."
    )

print(f"Loading model from {MODEL_PATH}…")
tokenizer = AutoTokenizer.from_pretrained(str(MODEL_PATH))
model     = AutoModelForSequenceClassification.from_pretrained(str(MODEL_PATH))
model.eval()

LABEL_MAP   = {"analysis": 0, "hot_take": 1, "reaction": 2}
ID_TO_LABEL = {v: k for k, v in LABEL_MAP.items()}

LABEL_DESCRIPTIONS = {
    "analysis":  "Structured argument backed by specific, verifiable evidence (stats, tactical observations, historical comparisons).",
    "hot_take":  "Bold opinion stated without meaningful supporting evidence — asserts rather than argues.",
    "reaction":  "Immediate emotional response to a specific event (goal, result, transfer, red card).",
}

LABEL_COLORS = {
    "analysis": "#2563eb",
    "hot_take": "#dc2626",
    "reaction": "#16a34a",
}

# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------

def classify(text: str) -> tuple[str, dict]:
    if not text.strip():
        return "<p style='color:#999'>Enter some text above.</p>", {}

    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=256)
    with torch.no_grad():
        logits = model(**inputs).logits

    probs   = F.softmax(logits, dim=-1)[0]
    pred_id = probs.argmax().item()
    pred    = ID_TO_LABEL[pred_id]
    conf    = probs[pred_id].item()
    scores  = {ID_TO_LABEL[i]: round(p.item(), 4) for i, p in enumerate(probs)}

    label_html = (
        f"<div style='font-size:1.5em; font-weight:bold; color:{LABEL_COLORS[pred]};'>"
        f"{pred.upper()}</div>"
        f"<div style='font-size:1.1em; margin:4px 0; color:#333;'>{conf:.1%} confidence</div>"
        f"<div style='color:#666; margin-top:6px;'>{LABEL_DESCRIPTIONS[pred]}</div>"
    )
    return label_html, scores

# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

with gr.Blocks(title="TakeMeter", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        "# TakeMeter\n"
        "### r/soccer Discourse Classifier — AI201 Project 3\n"
        "Paste any r/soccer post or comment to classify it as **analysis**, **hot_take**, or **reaction**."
    )

    with gr.Row():
        with gr.Column(scale=2):
            text_box = gr.Textbox(
                label="Post or comment",
                placeholder="Paste an r/soccer post here…",
                lines=4,
            )
            btn = gr.Button("Classify", variant="primary")

        with gr.Column(scale=1):
            label_out = gr.HTML(label="Prediction")
            score_out = gr.Label(label="Confidence scores", num_top_classes=3)

    gr.Examples(
        label="Try these examples",
        examples=[
            ["City's high line is why they're conceding headers — opponents win 68% aerial duels in the final third, up from 54% last year. Pep hasn't adjusted."],
            ["Is Ronaldo's hattrick vs Spain in 2018 the greatest ever??? Genuinely think no other player pulls that off in that moment."],
            ["THAT Bellingham header. What an absolute player. Can't believe what I just watched."],
            ["Ferran is such a bum — how does he keep getting called up to the national team?"],
            ["Germany's 7-1 means they've already matched the total big-margin wins from the entire 2018 and 2022 World Cups combined."],
        ],
        inputs=text_box,
    )

    btn.click(fn=classify, inputs=text_box, outputs=[label_out, score_out])
    text_box.submit(fn=classify, inputs=text_box, outputs=[label_out, score_out])

if __name__ == "__main__":
    demo.launch()
