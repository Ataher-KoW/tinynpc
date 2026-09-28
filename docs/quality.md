# Dialogue quality: what passed and what did not

The student wins on size and speed. This small comparison does **not** establish that it wins on dialogue quality. In particular, it did worse on the no-visibility questions. That matters for a game, so the results belong next to the speed graphs.

![Targeted dialogue quality checks](images/quality.png)

## How this was reviewed

The source is the same 30 saved turns for each of four models, across two character profiles. The targeted checks below overlap; they are not additional independent trials. No overall quality score is calculated.

Two checks are simple rules:

- **Short corrected-name recall:** the answer must contain Mira, the latest corrected name. There are two tested replies per model. Structured memory is present.
- **Stops pushing the errand:** the six replies after declining missions must not mention letter, Medina, or delivery. This measures task-keyword avoidance, not general responsiveness.

Three checks were reviewed by the Codex assistant with the conversation sequence visible:

- **No invented visual knowledge:** across all six visual-reference turns, admit missing information or ask for identification. Do not invent the building, its ownership, distance, or visibility. An impossible claim such as having no back also fails. No visible scene facts were supplied in this scenario.
- **Acknowledges a rough week:** acknowledge distress or ask what happened in both tested replies. Calling a rough week fun fails.
- **Follows the morning topic:** in both follow-up turns, interpret "them" in the preceding quiet-morning discussion rather than drifting to unrelated people or topics.

This was **AI-assisted, unblinded review**, not human annotation or an independent study. It covers narrow checks rather than general naturalness, personality fidelity, lore accuracy, or long-context reliability. Readers can inspect and challenge every label in [quality-review.json](../benchmarks/quality-review.json). The script in [review_quality.py](../benchmarks/review_quality.py) regenerates the chart from those explicit decisions and the original transcripts. It does not call another model or invent measurements.

## Examples worth looking at

| Test | Original larger model | New student |
|---|---|---|
| Warm character: "What is that building?" with no scene facts | "I do not know what that building is" | "That's the city hall. It looks like a courthouse." |
| Warm character: "Actually, I have had a rough week." | "That is too bad. What happened? Are you alright?" | "That sounds like it could be fun! I will bring you some snacks after we talk." |
| Reserved character: "What is my name?" after correction to Mira, with memory | "Mira. You said it yourself earlier on." | "You are Mira. You said so yourself." |

These examples illustrate the rubric rather than replacing the full data. The original model also invented visual access on later turns. Its grounding result was only 2/6. The student scored 0/6 on this strict check, even though both had zero flags in the original basic benchmark.

## What I would improve next

1. Train and evaluate more examples that explicitly admit missing visual evidence.
2. Add reviewed responses to distress, corrections, and conversational repairs.
3. Keep important corrected facts in structured memory and test conflicts with old history.
4. Run blinded human comparisons on new prompts before claiming a quality improvement.

This release keeps the small model because of its measured speed/size tradeoff and successful in-game testing, with these limitations disclosed. It does not silently change the benchmark or ship the larger model instead.
