# TakeMeter — Planning Document
## AI201 · Project 3

---

## Community: r/soccer

r/soccer is one of the largest sports communities on Reddit (~3.5M members), covering global football — Premier League, Champions League, World Cup, transfers, tactics, and match threads. The discourse is dense and varied: some posts are detailed tactical breakdowns, some are fiery one-liners, and many are pure emotional reactions to goals or results. The gap between a well-reasoned argument and a noise take is something regulars in the community notice and argue about constantly ("this sub is just vibes farming" vs. "actually engaging analysis"). That makes it a strong candidate for a discourse-quality classifier.

---

## Label Taxonomy

### Label 1: `analysis`

**Definition:** The post makes a structured argument supported by specific, verifiable evidence — statistics, tactical observations, historical comparisons, or formation/player role breakdowns. The reasoning is explicit: a claim is made and something concrete is offered in its support. Removing the opinion framing should still leave a meaningful, falsifiable argument standing.

**Examples:**
1. *"City's high line is the reason they're conceding so many headers this season — opponents are winning 68% of aerial duels in the final third against them, up from 54% last year. Pep hasn't adjusted and it's costing them points."*
2. *"People forget Dembélé has 16 assists in all competitions this season. His underlying numbers (xA, progressive carries into the box) are elite. The hate he gets is mostly based on his early injury record, not current form."*

**Uncertain example:** *"Rodri is the best defensive midfielder in the world right now — no one covers ground like him and his passing under pressure is unreal."*
→ Leans `hot_take` (superlative claim, vague "covers ground" phrasing, no numbers), but if a commenter added "his progressive pass completion rate under pressure is 91%" it would flip to `analysis`. **Decision rule:** if the evidence cited is specific and verifiable, label `analysis`; if it is impressionistic or qualitative without measurable grounding, label `hot_take`.

---

### Label 2: `hot_take`

**Definition:** A bold, confident opinion stated without meaningful supporting evidence. The post asserts rather than argues. The claim may or may not be true, but the post makes no real attempt to back it up — it relies on the reader's existing gut reaction. One cherry-picked stat used primarily for rhetorical effect (not as part of a chain of reasoning) still counts as a hot take.

**Examples:**
1. *"Mbappe is overrated. He disappears in big games and has never carried a team the way Messi or Ronaldo did."*
2. *"The Premier League is genuinely the worst-officiated top league in Europe. Every weekend it's an embarrassment."*

**Uncertain example:** *"Haaland only scores tap-ins — his xG conversion rate proves he's not elite, just clinical."*
→ This one cites "xG conversion rate" but uses it as a rhetorical flourish, not an actual argument. The post is still asserting (tap-in claim) without breaking down the data. **Decision rule:** a stat that supports a dismissive label without explaining the mechanism is still `hot_take`; a stat that forms the core of the reasoning chain is `analysis`.

---

### Label 3: `reaction`

**Definition:** An immediate emotional response to a specific event — a goal, result, red card, transfer announcement, press conference moment, or match incident. The post expresses a feeling in the moment with minimal to no structured argument. It may contain hyperbole, celebration, disbelief, or frustration, but the primary function is emoting rather than reasoning.

**Examples:**
1. *"THAT BELLINGHAM HEADER. WHAT A PLAYER OH MY GOD"*
2. *"Can't believe we conceded from a corner again. Same story, different week. Sack the manager."*

**Uncertain example:** *"Honestly if Arsenal lose this they deserve to be out of the title race — their squad depth has been exposed all season."*
→ This is triggered by a specific event (Arsenal losing a match) and expresses frustration, but it makes a structural claim about squad depth. **Decision rule:** if the post is primarily expressing a feeling about a specific event and the structural claim is a throwaway justification, label `reaction`. If the structural claim is elaborated with evidence or historical context, label `analysis` or `hot_take` accordingly.

---

## Edge Cases and Decision Rules

| Scenario | Rule |
|---|---|
| Post cites one stat but the claim is still assertive/dismissive | `hot_take` — one decorative stat ≠ analysis |
| Post triggered by a match but also makes a structured tactical point | `analysis` — the event is context, not the primary content |
| Post uses "always" / "never" hyperbole about a player | `hot_take` unless backed by longitudinal evidence |
| Post is a gif or image with a short caption | `reaction` — the primary content is the emotion |
| Post is a match thread top comment expressing disbelief | `reaction` |
| Post compares two eras of players with specific stats | `analysis` |

---

## Stretch Features Planned

- [ ] **Inter-annotator reliability** — have a second labeler annotate 30 examples; compute Cohen's kappa
- [ ] **Error pattern analysis** — systematically group wrong predictions by post length, label pair, and linguistic cues
- [ ] **Deployed interface** — Gradio app that accepts a Reddit post URL or text and returns label + confidence

---

## Milestone Checklist

- [x] Community chosen: r/soccer
- [x] Labels defined with one-sentence definitions
- [x] 2 clear examples per label
- [x] 1 uncertain example per label with written decision rule
- [x] Mutual exclusivity verified
- [ ] 200+ examples collected and annotated
- [ ] Train/val/test split documented
- [ ] Fine-tuning pipeline run
- [ ] Groq baseline run
- [ ] Evaluation report written
