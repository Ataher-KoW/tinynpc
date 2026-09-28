# Add TinyNPC to your game

## Architecture

Your game sends character information, the player's text, and a small set of visible scene facts. The runtime retrieves that NPC's memory, builds the dialogue context, and returns speech as plain text. One local model serves requests in sequence. This release does not implement a multiplayer scheduler.

Keep model choices inside `inference/`. Game code imports `create_dialogue_service` and `DialogueRequest` from the public `inference` package, or calls the HTTP bridge. Swapping weights should not require rewriting the game.

## Python

Run from the repository root:

```python
from inference import create_dialogue_service
from core.memory import MemoryStore
from core.runtime import NPCRuntime
from core.profile import NPCProfile
from core.personality import Personality
from core.perception import PerceptionFrame, PerceivedEntity

runtime = NPCRuntime(create_dialogue_service(), MemoryStore("data/my-game.db"))
npc = NPCProfile(
    npc_id="marcus", name="Marcus", role="city guard",
    personality=Personality(humor=87, bravery=79, friendliness=65),
).npc()
view = PerceptionFrame(entities=(
    PerceivedEntity("bakery", "building", "small stone bakery", 12, "left"),
))
try:
    result = runtime.talk_npc(npc, "player-1", "What is that building?", view)
    print(result.speech)
finally:
    runtime.close()
```

Hold onto the runtime while the game runs. Do not create it each frame or each turn. Run blocking calls on your own worker queue, and return UI updates to your engine's main thread. Call `close()` during shutdown.

## HTTP for other engines

Run `python -m core.http_api --port 8765`. Wait for `GET /health` to return `{"ready": true}`. Then send `POST /chat` with `Content-Type: application/json`. Use the request shown in the README.

The response contains:

```json
{
  "speech": "The bakery. It is just to the left.",
  "state": {"anger": 0, "respect": 50},
  "timings": {"context_seconds": 0.001, "generation_seconds": 0.25, "storage_seconds": 0.001, "total_seconds": 0.252}
}
```

This is an illustrative response shape, not a measured or guaranteed reply. State may contain additional fields. Preserve `npc.id` and `player_id` across turns so memory stays with the right conversation. The bridge accepts text up to 400 characters, up to 32 entities, and request bodies up to 16 KiB. It only binds to `127.0.0.1`. It is intended for a trusted game process on the same machine, not an exposed public service.

- **Unity:** use `UnityWebRequest` from a coroutine or async wrapper. Send UTF-8 JSON with `UploadHandlerRaw` and read `speech` from the response. A minimal helper is in [examples/unity/TinyNpcClient.cs](../examples/unity/TinyNpcClient.cs).
- **Unreal:** use the HTTP module and `FHttpModule::CreateRequest()`, set `POST` and the JSON content type, then parse `speech` in `OnProcessRequestComplete`. Add `HTTP`, `Json`, and `JsonUtilities` to your module dependencies.
- **Godot:** use an `HTTPRequest` node with `HTTPClient.METHOD_POST` and `JSON.stringify(payload)`. Read the result in `request_completed` and update your dialogue UI.

The HTTP protocol was smoke-tested locally. Engine editor builds and packaging are not tested in this release. Ship the Python bridge as a sidecar process, or write your own native integration against the local inference server. Launch it once, wait for readiness, and stop your owned process during game shutdown.

## Point of view

Your engine already knows where things are. Use the NPC camera's frustum, distance checks, and raycasts to decide what is visible. Send a handful of relevant entities with their descriptions, distance in metres, and direction relative to the NPC. Do not send hidden quest answers or objects behind walls as visible facts.

The runtime excludes entities marked `visible: false`, prioritizes relevant nearby objects, and asks for clarification when a reference is ambiguous. Python callers can set `focused_entity_id` when the player explicitly points at a visible object. See [examples/scene.json](../examples/scene.json).

An optional `caption` is text supplied by your game or your own vision system. **The model cannot read image pixels.** Python's `PerceptionFrame.image_path` can associate a local screenshot with a turn for your own records, but it still needs visible entities or a caption. The HTTP bridge intentionally accepts descriptions and captions instead of arbitrary local file paths.

## Personality and memory

Personality fields are `humor`, `bravery`, `friendliness`, `patience`, `aggressiveness`, `honesty`, `curiosity`, and `sociability`, each from 0 to 100. Optional `npc.style` fields are `swearing`, `sarcasm`, and `verbosity`. They shape the prompt; they do not produce mathematically exact behavior.

Memory uses SQLite and is separated by NPC and player. Recent history retains up to 12 exchanges, with token budgeting trimming the oldest complete pairs when needed. Clear name statements such as "Call me Dev" become player claims. Host facts, player claims, and interactions remain distinct. No embedding model is required.

For authored facts in Python, call `runtime.memory.remember(npc_id, player_id, key, value, source="host")`. For temporary events use `remember_event` with a TTL. Use `forget` to remove outdated facts. Back up the SQLite database if you want to keep conversations across saves. Never publish your users' memory database with your game source.

## Runtime and other platforms

`python -m inference.setup --runtime windows-cuda` installs the pinned Windows CUDA 12.4 runtime and its required libraries. Keep a compatible NVIDIA driver installed. This setup was tested with an RTX 2060 6 GB. CPU-only Windows setup is `python -m inference.setup --runtime windows-cpu`; its speed is unmeasured.

On Linux or macOS, download the model with `python -m inference.setup`, obtain or build `llama-server` from the [pinned upstream release](https://github.com/ggml-org/llama.cpp/releases/tag/b11060), and update `server_path` in `inference/config.json`. Use the appropriate upstream CUDA, Vulkan, Metal, or CPU build. Cross-platform execution is supported by the Python design but has not been validated here.

`model_path` and `server_path` resolve relative to `inference/`, or can be absolute. `context_tokens` defaults to 8192 in the release config. `gpu_layers` controls offloading, `threads` controls CPU threads, and `flash_attention` is passed to the native runtime. Start with the supplied settings. A larger context consumes more memory and can increase prefill time. Lower it to 2048 if you want to reproduce the main comparison.

If startup fails, read `data/gpu-server.log`. Missing DLLs usually mean the native runtime or CUDA runtime archive was not installed completely. Out-of-memory errors can require a smaller context or less GPU offloading. Those changes may affect speed. The Python wrapper does not require PyTorch, Transformers, speech models, or a Rust toolchain.
