"""Engine-neutral observations. Hosts determine visibility; hidden knowledge stays out."""
from dataclasses import dataclass
from pathlib import Path
import math
import re


@dataclass(frozen=True)
class PerceivedEntity:
    entity_id: str
    kind: str
    description: str
    distance: float
    direction: str = "ahead"
    known_name: str = ""
    activity: str = ""
    visible: bool = True

    def __post_init__(self):
        if not self.entity_id.strip():raise ValueError('Entity ID is required.')
        if not math.isfinite(self.distance) or self.distance<0:raise ValueError('Entity distance must be finite and nonnegative.')

    def describe(self):
        label = self.known_name or self.description or self.kind
        if self.known_name and self.description and self.description.casefold()!=self.known_name.casefold():
            label=self.known_name+' ('+self.description+')'
        activity = f", {self.activity}" if self.activity else ""
        return f"{label[:90]}, {self.direction}, {self.distance:.0f} metres away{activity[:60]}"


@dataclass(frozen=True)
class PerceptionFrame:
    entities: tuple[PerceivedEntity, ...] = ()
    location: str = ""
    image_path: str = ""
    # A host-provided caption is provenance-labelled; pixels are not interpreted here.
    caption: str = ""
    focused_entity_id: str = ""

    def __post_init__(self):
        ids=[e.entity_id for e in self.entities]
        if len(set(ids))!=len(ids):raise ValueError('Entity IDs must be unique.')

    def resolve(self,query,previous_id=""):
        """Return a visible target, ambiguity, or unknown; never select hidden entities."""
        visible=[e for e in self.entities if e.visible]
        if self.focused_entity_id:
            focused=next((e for e in visible if e.entity_id==self.focused_entity_id),None)
            if focused:return focused,'explicit'
        words=set(re.findall(r'[a-z]+',query.lower()))
        if re.search(r'\bmy (?:left|right)\b',query,re.I):return None,'unknown'
        # Resolve spatial constraints before selecting a kind or an old topic.
        # A visible object elsewhere is not evidence for the requested side.
        spatial=re.search(r'\b(?:on|to|at|toward|towards)\s+(?:(?:your|my|the)\s+)?(left|right|north|south|east|west)\b',query,re.I)
        direction=spatial[1].lower() if spatial else ('behind' if re.search(r'\bbehind (?:you|us|me)\b',query,re.I) else 'ahead' if re.search(r'\b(?:in front of you|straight ahead)\b',query,re.I) else '')
        if direction:
            candidates=[e for e in visible if direction in e.direction.lower().split() or (direction=='ahead' and e.direction.lower()=='front')]
            kinds={'building','structure','house','person','prop','object'} & words
            kind='building' if kinds & {'building','structure','house'} else 'person' if 'person' in kinds else None
            if kind:candidates=[e for e in candidates if e.kind==kind]
            if not candidates:return None,'missing'
            nouns=words-{'a','an','the','is','it','you','your','my','on','to','at','of','structure','building','object',direction}
            named=[e for e in candidates if nouns & set(re.findall(r'[a-z]+',(e.known_name+' '+e.description).lower()))]
            if len(named)==1:return named[0],'named'
            if len(candidates)==1:return candidates[0],'spatial'
            return None,'ambiguous'
        stop={'what','where','which','that','this','there','your','like','with','have','does','about','person','building'}
        nouns=words-stop
        matches=[e for e in visible if nouns & set(re.findall(r'[a-z]+',(e.known_name+' '+e.description).lower()))-{'a','an','the','of','to','in','on','is','it','you'}]
        if len(matches)==1:return matches[0],'named'
        if len(matches)>1:return None,'ambiguous'
        for kind in ('building','person','prop'):
            if kind in words or (kind=='building' and 'structure' in words):
                matches=[e for e in visible if e.kind==kind]
                if len(matches)==1:return matches[0],'unique'
                if len(matches)>1:return None,'ambiguous'
                return None,'missing'
        if words & {'it','that','this'}:
            previous=next((e for e in visible if e.entity_id==previous_id),None)
            if previous:return previous,'previous'
            return None,'unknown'
        if re.search(r'\b(?:can you see|do you see|can you identify|can you make out)\b',query,re.I):return None,'missing'
        return None,'none'

    def observations(self, query="", limit=4):
        words = set(query.lower().split()) - {"the", "a", "you", "is", "it", "that"}
        visible = [e for e in self.entities if e.visible and e.distance >= 0]
        target,_=self.resolve(query)
        visible.sort(key=lambda e: (e is not target,-len(words & set(e.describe().lower().split())), e.distance))
        result = [e.describe() for e in visible[:limit]]
        if self.location:result.insert(0,'Current location: '+self.location[:160])
        if self.caption:
            result.append("Host-provided image caption: " + self.caption[:180])
        if self.image_path and not (visible or self.caption):
            raise ValueError("An image needs visible scene entities or a host caption; pixel understanding is not enabled.")
        if self.image_path and not Path(self.image_path).is_file():
            raise ValueError("The perception image does not exist.")
        return tuple(result[:limit+2])
