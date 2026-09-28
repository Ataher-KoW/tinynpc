# Design an NPC in JSON

There are three inputs. Your character definition says **who the NPC is**. The current POV says **what the NPC can see**. The player message says **what the player is asking**. TinyNPC combines them for each reply.

```text
NPC definition + current POV + player message + relevant memory
                              |
                              v
                      In-character reply
```

## 1. Define the character once

Save this as a JSON file in your own game project:

```json
{
  "id": "marcus",
  "name": "Marcus",
  "role": "city guard",
  "description": "Marcus grew up in Northbridge. He guards the east gate, enjoys baking bread, and uses gentle humor. He is patient when someone needs help.",
  "personality": {"humor": 70, "bravery": 79, "friendliness": 75, "patience": 85},
  "style": {"verbosity": 30, "sarcasm": 15, "swearing": 0},
  "known_facts": ["The east gate closes at dusk."],
  "conversation_style": ["Speak casually. Be sincere when someone is upset."]
}
```

`description` is the character's background and manner, up to 1,000 characters. It is included on every turn rather than waiting for memory retrieval. `known_facts` holds up to 20 short authored facts, which enter the NPC's memory and are selected when relevant. `conversation_style` holds up to four short delivery notes. Personality and style values run from 0 to 100. They guide the reply, but they do not guarantee an exact personality score.

Keep descriptions focused. State useful facts and how the character talks. You do not need a page of prompt instructions or a new trained model for each NPC. Reuse the same model with a different JSON definition. Stable `id` values keep each NPC's memory separate.

Ready-to-edit examples: [Marcus](../examples/npcs/marcus.json), [Lena](../examples/npcs/lena.json). The optional [JSON schema](../examples/npc.schema.json) can help your editor validate definitions.

## 2. Send the current POV

```json
{
  "location": "East gate square",
  "entities": [
    {"id": "player", "kind": "person", "description": "the player", "distance": 2, "direction": "ahead", "activity": "speaking to you"},
    {"id": "bakery", "kind": "building", "description": "small stone bakery", "distance": 12, "direction": "left"}
  ]
}
```

Update this as the NPC or world moves. Your engine decides visibility using its camera, distances, and line-of-sight checks. Give entities stable IDs and brief descriptions. People can also have a `name` and `activity`. Mark hidden entities `visible: false`, or leave them out entirely. An optional `focused_entity_id` identifies a visible object the player is pointing at. `caption` can supply a short description produced by your engine or a separate vision system.

**POV here means text scene context, not raw image understanding.** The model reads the descriptions. It does not inspect screenshot pixels. See [the sample POV](../examples/pov/east-gate.json).

## 3. Add the player's message

Send the loaded objects to the local bridge:

```python
payload = {
    "npc": npc_definition,
    "pov": current_pov,
    "player_id": "player-1",
    "text": "Hello, how are you?"
}
```

Conceptually, the model receives this:

```text
Character: You are Marcus, a city guard.
Background: You grew up in Northbridge, enjoy baking bread, and are patient.
Current scene: East gate square. The player is 2 metres ahead and speaking
to you. A small stone bakery is 12 metres to your left.
Style: Keep the reply short and natural. Use background only when relevant.
Player: Hello, how are you?
```

This is a readable illustration, not the exact internal prompt. The runtime also adds state, relevant memories, recent conversation, and output-format instructions. Character information goes in the system context. The player's words stay in a separate user message. Developers supply the trusted definition and scene; players supply only their dialogue text.

## Try the supplied files

After model setup, start `python -m core.http_api`. In a second terminal run `python -m examples.designed_npc`. The example loads Marcus and the east-gate POV from JSON and sends your text to the bridge. Change the JSON file selection to Lena to try a different character. Restart the example after editing a file so it reloads.

Python games can use `NPCProfile.from_dict(npc_definition)` and `runtime.talk_profile(profile, player_id, text, perception)`. `NPCSession.reply` uses the same path. `talk_profile` updates authored facts when the profile changes, including removing facts no longer present, while keeping other memories intact. The lower-level `talk_npc` API does not synchronize a profile's known-fact list.

For HTTP, send the complete current `npc` definition on each request. Omitting `known_facts` means an empty list and removes previous profile facts for that NPC/player pair. This avoids old authoring data silently surviving an edited character.
