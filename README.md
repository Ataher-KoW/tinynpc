# TinyNPC: an NPC-ready LLM for games with fast local responses

I wanted NPCs I could actually talk to. Small enough to ship, quick enough to keep a conversation moving, and simple enough to drop into a game.

TinyNPC is a **1.28 GB local dialogue model** with a lightweight integration for character personality, memory, and the things an NPC can see around it. On my **RTX 2060 6 GB**, the new model averaged **0.246 seconds per text reply** across 30 test turns. No cloud API or paid inference service is required.

**[Download the model](https://github.com/Ataher-KoW/tinynpc/releases/tag/v0.1.0)** | **[Game integration](docs/integration.md)** | **[Results and limits](docs/benchmarks.md)** | **[Model card](inference/MODEL_CARD.md)**

![TinyNPC model size and response time comparisons](docs/images/overview.png)

## What you get

- Short, in-character text replies from one shared local model.
- Personality controls such as humor, bravery, friendliness, and patience, from 0 to 100.
- Separate conversation memory for each NPC and player.
- Point-of-view context: visible entities, distance, direction, and an optional game-provided caption.
- A Python API, a local HTTP API, a terminal demo, and benchmark data you can inspect.

This release is text only. Bring your own game, speech system, and UI. The game stays in charge of visibility and actions. The model produces dialogue; it cannot move characters or change your world by itself.

## Try it

The automatic setup below is for **Windows x64 with an NVIDIA GPU**, using Python 3.10 or newer. This is the path tested on my PC. CPU and other platforms are covered in [integration](docs/integration.md).

```powershell
git clone https://github.com/Ataher-KoW/tinynpc.git
cd tinynpc
python -m inference.setup --runtime windows-cuda
python -m examples.chat
```

Setup downloads the model, verifies its checksum, and installs the pinned native runtime. The Python runtime code itself uses only the standard library. The **1.28 GB number is the model file**, not the full installation. The Windows CUDA runtime archives add about **646 MB of downloads** and need more space after extraction. Allow at least 4 GB of free disk space for installation.

If a download is interrupted, run setup again. It resumes a partial download and verifies the complete file. Already have a compatible native runtime? Use `python -m inference.setup`, then set its path in `inference/config.json`.

## Put it in your game

Start the local bridge:

```powershell
python -m core.http_api
```

Send JSON to `http://127.0.0.1:8765/chat`:

```json
{
  "player_id": "player-1",
  "npc": {
    "id": "marcus",
    "name": "Marcus",
    "role": "city guard",
    "personality": {"humor": 87, "bravery": 79, "friendliness": 65}
  },
  "text": "What is that place on your left?",
  "visible_entities": [
    {"id": "bakery", "kind": "building", "description": "small stone bakery", "distance": 12, "direction": "left"}
  ]
}
```

Read `speech` from the response and show it in your dialogue UI. Send requests asynchronously so your game keeps rendering. Use one bridge for all NPCs, rather than loading a separate model for every character. See [the full guide](docs/integration.md) for Python, Unity, Unreal, Godot, memory, and point-of-view setup.

## How fast is it?

All four rows below were measured on the same RTX 2060. These are variants from this project, not a comparison against every NPC model out there. Smaller and lower latency are better.

| Model | File size, decimal GB | Mean text turn | Median | p95 | Basic flags / 30 |
|---|---:|---:|---:|---:|---:|
| **TinyNPC student** | **1.282** | **0.246 s** | **0.255 s** | **0.361 s** | **0** |
| Calibrated larger model, Q4_K_S | 2.383 | 0.321 s | 0.308 s | 0.460 s | 0 |
| Original larger model, Q4_K_M | 2.497 | 0.352 s | 0.340 s | 0.494 s | 0 |
| Calibrated larger model, IQ3_M | 1.963 | 0.414 s | 0.408 s | 0.568 s | 1 |

The student has **49% less file size and 30% lower mean latency** than the original model in this test. Timing includes the text generation and memory/context work. It excludes startup, rendering, and speech. Replies vary in length. This is one run of 30 turns per model, not a hardware-wide guarantee.

![Distribution of measured text turn times and response lengths](docs/images/turns.png)

## And the dialogue quality?

The smaller model is faster, but it is not a clean quality win. I added a separate review because zero basic flags missed some bad replies, especially made-up visual details.

![Targeted dialogue quality comparison](docs/images/quality.png)

These are small, targeted checks from the same saved conversations. Some use simple rules; others were reviewed by the Codex assistant, not human raters. See [the rubric, exact replies, and failures](docs/quality.md). I am publishing the tradeoff, not calling this perfect dialogue.

## What still needs work

I like where this is now, but I do not want to sell you a perfect-human claim. Odd questions can still get awkward answers. Mood and personality controls are guidance, not exact guarantees. A longer test still used an old name after the player corrected it when structured memory was absent. The regular memory-assisted name test passed.

The integration enables an 8K context window. That means capacity, not proven perfect recall over 8K tokens. The comparison table used 2K context for all models. Additional student probes ran at 8K capacity without filling the whole window.

The RTX 2060 is the only GPU measured here. I have not measured other GPUs, CPU-only performance, many simultaneous players, or phone hardware. Test your target hardware with `python -m benchmarks.run`.

## What is in the release?

The download is **1,282,438,944 bytes**, or **1.282 GB / 1.194 GiB**. Only the student weights are published. No larger teacher weights, voice models, private conversations, training checkpoints, or development environment are included.

Benchmark transcripts and timing data are in [benchmarks/results](benchmarks/results). They are synthetic test conversations. Training data provenance and licenses are explained in the [model card](inference/MODEL_CARD.md); raw training corpora are not bundled.

## Development

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m benchmarks.plot
```

The integration code is MIT licensed. The model derives from an Apache-2.0 base; its license and modification notice are included under `inference/`. See [third-party notices](NOTICE.md).
