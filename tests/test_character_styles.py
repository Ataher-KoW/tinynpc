from dataclasses import asdict
from core.profile import NPCProfile,character_traits
from core.personality import Personality, SpeechStyle


def test_three_styles_reach_dialogue():
    profiles={
        'marcus':NPCProfile(personality=Personality(patience=90),speech=SpeechStyle(sarcasm=90)),
        'elena':NPCProfile(personality=Personality(curiosity=90),speech=SpeechStyle(verbosity=90)),
        'samir':NPCProfile(personality=Personality(sociability=90),speech=SpeechStyle(verbosity=10)),
    }
    styles={key:character_traits(profile.npc()) for key,profile in profiles.items()}
    assert 'dry sarcasm' in styles['marcus']
    assert 'patient' in styles['marcus']
    assert 'curious about people' in styles['elena']
    assert 'longer replies when useful' in styles['elena']
    assert 'enjoys conversation' in styles['samir']
    assert 'impatient' not in styles['samir']
    assert 'brief replies' in styles['samir']
    assert len(set(styles.values()))==3


def test_style_profile_roundtrip():
    original=NPCProfile(conversation_style=('Dry wit, gentle teasing.',))
    restored=NPCProfile.from_dict(asdict(original))
    assert restored.npc().conversation_style==original.conversation_style
    assert 'Dry wit, gentle teasing.' in character_traits(restored.npc())
