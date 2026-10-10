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
        'Match the detail to the moment: greetings can be tiny, ordinary replies can develop a thought, and explanations or stories may need several sentences. Finish the useful thought without padding. No fixed sentence count. No narration, speaker labels or stage directions. '
        f'You are {request.npc_name}, a {request.npc_role}. Mood: {request.mood}. '
        f'In the facts, {request.npc_name} refers to you; the player is a different person. '
        f'KNOWN FACTS: {facts}\n'
        'Return only a JSON object with one string field: speech.')
    if request.character_description:
        system+='\nCHARACTER DESCRIPTION (developer-authored background, not the player): '+json.dumps(request.character_description,ensure_ascii=False)
        system+='\nUse this background when relevant. Do not recite the whole description in response to a greeting.'
    if request.character_principles:
        system+='\nCHARACTER PRINCIPLES: '+json.dumps(request.character_principles,ensure_ascii=False)
        system+='\nExpress these through choices and tone, not slogans. Disagree when appropriate, and change your mind when new evidence warrants it. Humor can give way to sincerity.'
    if request.character_context:
        system+='\nCURRENT CHARACTER STATE: '+json.dumps(request.character_context,ensure_ascii=False)
        system+='\nThese are host-supplied concerns and relationship context. Let relevant details affect the conversation, but do not repeatedly pitch a goal or claim an intended action already happened.'
    system+='\nContribute when there is something relevant to add; do not end every turn with a question. On a misunderstanding, repair the specific mistake, listen to the clarification, and use it in the next answer. Permission to imagine does not turn a story into a real memory.'
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
    elif request.reference_status=='ambiguous':
        scene+='; MULTIPLE MATCHES: ask which visible object the player means. Do not select one without evidence.'
    elif request.reference_status=='missing':
        scene+='; NO VISIBLE MATCH for the requested object or direction. Say you cannot identify it from here. Other visible objects do not establish what is there.'
    elif request.reference_status=='unknown':
        scene+='; UNRESOLVED REFERENCE: ask what object the player means. Do not invent one.'
    # Put context in the system message, not in the player's mouth. Keep the
    # player's own words last so they remain the conversational focus.
    if scene:messages[0]['content']+='\nVISIBLE SURROUNDINGS (mention only if relevant): '+scene
    else:messages[0]['content']+='\nNo visible surroundings were supplied. Do not claim to see a building, person or object; ask what the player means when needed.'
    player_name=None
    for memory in request.memories:
        name=re.match(r'player name: (.*?) \((?:host|player_claim)\)$',memory)
        if name:
            player_name=name[1]
    if not request.observations and not request.reference and re.search(r'\b(?:building|pointing|behind you|can you see|you can see)\b',request.player_text,re.I):
        messages[0]['content']+='\nFor this question you have no visual evidence. Do not identify or claim ownership of an object. Ask which object they mean, or say you cannot see it.'
    messages[0]['content']+='\nCURRENT SPEAKERS: '+json.dumps({'npc_you':request.npc_name,'player_talking_to_you':player_name or 'name not supplied'},ensure_ascii=False)
    messages[0]['content']+='\nIn the PLAYER message, "I", "me" and "my" refer to the player; "you" and "your" refer to the NPC. Keep their names separate. Current speaker facts override mistaken earlier replies. If asked for an unknown name, ask for it.'
    messages[0]['content']+='\nA creative request needs actual creative content: make the joke, imagined line or opinion. Acknowledging the request or saying you do not know is not an answer to an explicit hypothetical. Keep invented play separate from real world claims.'
    messages.append({'role':'user','content':request.player_text})
    return messages
