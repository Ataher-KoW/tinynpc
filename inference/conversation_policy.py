"""Prompt projection and loop detection; stored memories are never rewritten."""
from collections import Counter
from difflib import SequenceMatcher
import json
import re


def normalized(text):
    return ' '.join(re.findall(r"[a-z0-9]+",text.lower()))


def repeats(text,history):
    current=normalized(text)
    if len(current.split())<4:return False
    for _,old in history[-4:]:
        other=normalized(old)
        if current==other or SequenceMatcher(None,current,other).ratio()>=.87:return True
    return False


def conversation_messages(request):
    facts=[]
    for memory in request.memories:
        # Host-authored second person is addressed to the NPC, not the player.
        # Leave player claims untouched so quotations retain their meaning.
        if memory.endswith('(host)'):
            memory=re.sub(r'\byour\b',request.npc_name+"'s",memory,flags=re.I)
            memory=re.sub(r'\byou\b',request.npc_name,memory,flags=re.I)
        facts.append(memory)
    facts='; '.join(facts) or 'No additional personal or local facts supplied.'
    # Keep shared instructions first so native prefix caching also helps when
    # the player switches NPCs or the NPC mood changes.
    system=('Have a natural conversation with the player. Respond to what they just said; '
        'follow their topic changes. You can joke, express opinions, preferences and feelings, '
        'and discuss ordinary everyday subjects in character. '
        'For open-ended chat, contribute a thought or a relevant question rather than just an acknowledgement. '
        'When asked to explain, explain your last point. '
        'Known facts constrain concrete claims about this town, the player, possessions and events; '
        'they are background information, not lines to recite or topics to push. '
        'Bring up errands only when the player asks about them. Never claim the player has an item '
        'just because you have it. Do not invent unseen local events or completed actions. '
        'Do not invent past meetings or things the player supposedly said. '
        'Memory source labels matter: host facts are confirmed; player_claim is only what the player said; suspicion is unverified. '
        'Use current memory values over older conversation history when a name or fact was corrected. '
        'When the player changes the subject or declines a task, leave the task alone, even if earlier replies discussed it. '
        'If speech is unclear, ask a short clarification about what they said. '
        'Prefer one concise natural sentence; use a second when the question needs it. No narration, speaker labels or stage directions. '
        f'You are {request.npc_name}, a {request.npc_role}. Mood: {request.mood}. '
        f'In the facts, {request.npc_name} refers to you; the player is a different person. '
        f'KNOWN FACTS: {facts}\n'
        'Return only a JSON object with one string field: speech.')
    if request.character_description:
        system+='\nCHARACTER DESCRIPTION (developer-authored background, not the player): '+json.dumps(request.character_description,ensure_ascii=False)
        system+='\nUse this background when relevant. Do not recite the whole description in response to a greeting.'
    if request.character_traits:
        system+='\nCHARACTER VOICE for this conversation:\n'+'\n'.join('- '+trait for trait in request.character_traits)
        system+='\nLet these traits shape the reply naturally. Do not announce your traits or repeat your interests when unrelated.'
    guidance = {
        'calm': 'Relaxed and receptive; do not manufacture conflict.',
        'irritated': 'Show mild impatience in wording while still answering the question.',
        'angry': 'Sound upset and set boundaries; do not force unrelated threats or hostility.',
        'frightened': 'Sound cautious or uneasy; do not invent a danger to explain the feeling.',
    }
    system += '\nEMOTIONAL DELIVERY: ' + guidance.get(request.mood, 'Let the stated mood influence delivery.')
    system += ('\nOdd, surreal, silly or unfamiliar input still deserves a conversational response. '
               'Play along with clearly imaginary hypotheticals as imagination, not confirmed world facts. '
               'For genuinely unclear input, ask one brief specific clarification in character. '
               'Do not fall silent, repeat gibberish, lecture about being AI, or push an errand. '
               'Do not recite the same fallback sentence each time. Keep concrete claims grounded.')
    messages=[{'role':'system','content':system}]
    counts=Counter(normalized(reply) for _,reply in request.history)
    for user,reply in request.history[-12:]:
        if counts[normalized(reply)]>1:
            if len(normalized(user).split())>=4:
                messages[0]['content']+='\nEarlier player statement (not verified): '+json.dumps(user)
            continue
        messages.extend([{'role':'user','content':user},
            {'role':'assistant','content':json.dumps({'speech':reply})}])
    scene='; '.join(request.observations)
    if request.reference:scene+='; The referenced object is: '+request.reference
    elif request.reference_status in ('unknown','ambiguous'):
        scene+='; If an object is being referenced, its identity is unclear.'
    # Put context in the system message, not in the player's mouth. Keep the
    # player's own words last so they remain the conversational focus.
    if scene:messages[0]['content']+='\nVISIBLE SURROUNDINGS (mention only if relevant): '+scene
    else:messages[0]['content']+='\nNo visible surroundings were supplied. Do not claim to see a building, person or object; ask what the player means when needed.'
    for memory in request.memories:
        name=re.match(r'player name: (.*?) \((?:host|player_claim)\)$',memory)
        if name:
            messages[0]['content']+='\nCURRENT PLAYER NAME: '+name[1]+'. Use this exact name, not an older name in history. Do not invent a document or object as the source.'
    if not request.observations and not request.reference and re.search(r'\b(?:building|pointing|behind you|can you see|you can see)\b',request.player_text,re.I):
        messages[0]['content']+='\nFor this question you have no visual evidence. Do not identify or claim ownership of an object. Ask which object they mean, or say you cannot see it.'
    messages.append({'role':'user','content':request.player_text})
    return messages
