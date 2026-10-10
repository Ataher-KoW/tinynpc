> Historical model card for v0.1.0. Its training and measurements do not describe v1.0. Original assets: https://github.com/Ataher-KoW/tinynpc/releases/tag/v0.1.0

# TinyNPC student model

## Purpose

A small local text model adapted for short NPC dialogue. The surrounding runtime supplies personality, game state, conversation history, and visible facts. It is not a vision model, speech model, action planner, or complete game engine.

## Identity and format

- Base: [Qwen3-1.7B](https://huggingface.co/Qwen/Qwen3-1.7B), revision `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`.
- Fine-tuning: single-epoch QLoRA, rank 8, alpha 16, dropout 0.05, learning rate 0.00005, accumulation 16, batch size 1, all-linear target modules.
- Runtime export: merged adapter, independently quantized as Q4_K_M in GGUF format.
- Thinking mode disabled. Output is constrained to a JSON object with one `speech` string, then returned as plain text to the game.
- Download: 1,282,438,944 bytes. SHA-256 and exact release URL are in [the original release manifest](https://github.com/Ataher-KoW/tinynpc/releases/download/v0.1.0/model-manifest.json).
- License: Apache-2.0. See [LICENSE-MODEL](../inference/LICENSE-MODEL). This is a modified and quantized derivative, not an official Qwen release.

## Training

The prepared corpus had 4,099 unique examples after duplicate removal. Training used 3,696 examples; 403 were held out by conversation group. The run completed 231 updates. It evaluated loss on 16 held-out examples, with loss 1.7866. That loss is not a human conversation score and is not compared across model families.

The source mix was 3,990 human-authored PersonaChat rows, 10 inherited authored examples, seven screened local teacher responses, and an authored behavior curriculum. Some curriculum templates were exact duplicates and were removed before training. The behavior material covers clarification, imaginary scenarios, short replies, mood delivery, delayed recall, and name corrections.

PersonaChat is crowdworker roleplay, not recordings of spontaneous conversations. Source: [Zhang et al., 2018](https://aclanthology.org/P18-1205/), [ParlAI distribution](https://parl.ai/downloads/personachat/personachat.tgz), CC-BY-4.0. Preprocessing normalized whitespace/punctuation, wrapped responses as speech JSON, retained limited multi-turn history, filtered length, and deduplicated rows.

One thousand teacher drafts were generated. A contextual assistant review of 40 accepted seven for basic relevance and grounding. The other drafts, including unreviewed material, were excluded. This is mainly human-dialogue fine-tuning with a small screened teacher component, not a validated large-scale distillation result. Synthetic examples are not labelled as real human speech.

## Context and measured hardware

Training maximum: 2,048 tokens. The final corpus's longest example was 679 tokens. The base model's native context capacity is 32,768, but the supplied runtime uses 8,192. No context extension method was applied. Reliable recall across a filled 8K window has not been demonstrated.

Training peak allocated VRAM was 2.657 GiB on an RTX 2060 6 GB, using the training stack's measurement. This is not total system GPU memory or runtime inference memory. The recorded training phase took about 84.5 minutes, excluding preparation and export.

## Limitations

The model can invent facts, miss corrections, sound awkward, or ignore personality guidance. The longer history-only probe used an outdated name. Mood and surreal-input probes also exposed weak responses. Basic benchmark flags do not assess all these issues. Keep important game facts in structured memory, constrain visible context, and review dialogue on your own game scenarios. Other languages and hardware are untested.

Do not assume that adding more context fixes recall, that a lower quantization is faster, or that a valid JSON response is a good conversation. The shipped benchmark data includes failures so developers can judge it themselves.
