# Notices and attribution

TinyNPC integration code: Copyright 2026 Ataher-KoW, MIT license.

The downloadable student model is a fine-tuned and Q4_K_M-quantized derivative of Qwen3-1.7B. Base model copyright: Alibaba Cloud. The upstream Apache-2.0 license is retained in `inference/LICENSE-MODEL`. Changes: dialogue fine-tuning, merged adapter, GGUF conversion, and quantization. The model is not affiliated with or endorsed by its upstream authors.

Human dialogue source: Saizheng Zhang, Emily Dinan, Jack Urbanek, Arthur Szlam, Douwe Kiela, and Jason Weston. 2018. Personalizing Dialogue Agents: I have a dog, do you have pets too? ACL 2018. PersonaChat, distributed via ParlAI under CC-BY-4.0. See https://aclanthology.org/P18-1205/ and https://parl.ai/downloads/personachat/personachat.tgz. Raw training data is not redistributed in this repository. The model card describes preprocessing and synthetic examples.

Native inference uses llama.cpp under its upstream MIT license. Setup downloads official release assets separately and preserves license files found in the archives. See https://github.com/ggml-org/llama.cpp and https://github.com/ggml-org/llama.cpp/blob/master/LICENSE.

Benchmark conversations in this repository are synthetic local evaluation material. They do not contain the developer's private in-game conversation history. Chart code uses matplotlib as a development dependency; matplotlib is not needed to run dialogue.

IFEval: Jeffrey Zhou and colleagues, Instruction-Following Evaluation for Large Language Models (2023), Google Research. Official scorer and evaluation prompts are Apache-2.0. Downloaded source retains its notices. Published evaluation records reproduce benchmark prompts for auditability; see https://github.com/google-research/google-research/tree/master/instruction_following_eval. The Apache-2.0 license text is included in inference/LICENSE-MODEL.
