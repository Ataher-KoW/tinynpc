# TinyNPC v1.0 student model

A local text model for NPC dialogue, conditioned on character descriptions, game state, history, memory and structured visible facts. It is not a vision or speech model.

## Identity

- Base family: Qwen/Qwen3-1.7B, inherited base revision `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`.
- This release continues a previously fine-tuned student with supervised fine-tuning and SimPO preference tuning. It was not trained from scratch.
- The preference adapter selected at step 75 was merged and quantized as Q4_K_M GGUF.
- Size: 1,282,438,944 bytes. Exact checksum and part URLs: [model-manifest.json](model-manifest.json).
- Modified Apache-2.0 derivative, not an official Qwen release. See [LICENSE-MODEL](LICENSE-MODEL).
- No teacher weights, speech assets or training corpora are distributed.

## Latest training stages

SFT used 6,590 prepared examples and completed 412 updates; the selected adapter was step 375. The report sampled 128 development examples and records best development loss 1.0055. Preference tuning used 1,348 pairs and completed 85 updates; the selected adapter was step 75. Its development sample contained 64 examples and best loss was 1.2392. Losses across different objectives are not comparable quality scores.

The new conversation material is synthetic teacher-generated dialogue, not recordings of real people. Student alternatives support preference construction. The inherited student also used human-authored dialogue; see [the historical model card](../docs/model-card-v0.1.md) and repository notices for that earlier provenance. This release does not establish independent human validation of the synthetic corpus.

Both stages used parameter-efficient adapters. The latest training limit was 4,096 tokens. The integration config uses an 8,192-token context capacity; reliable recall across a filled window has not been demonstrated.

## Evaluation and selection

See [v1.0 measurements](../docs/v1.0.md) and [raw summary statistics](../benchmarks/v1.0/statistics.json). The owner chose these weights after an in-game trial. Automatic selection rejected them for worse narrow corrected-name/current-view checks and short-reply p95 latency. The 600-case test of the automatically selected model does not evaluate this release's preference weights.

The development AI preference score was 0.750 over 100 conversations. This is not human accuracy. The same teacher contributed training material and evaluation, which can bias results. No independent superiority claim is made.

## Limitations

Replies can hallucinate facts, miss corrections, leak markup or stage directions, and drift from character instructions. The unedited demo includes such a formatting leak. JSON-constrained output does not guarantee clean natural speech inside the string. Keep authoritative game actions and state outside the model. Only RTX 2060 6 GB performance has been measured locally. Speech, startup, and other hardware are excluded from timing claims.
