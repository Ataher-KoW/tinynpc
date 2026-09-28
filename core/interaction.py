"""Small transparent classifier; heuristic, not general language understanding."""
import re
from .response import Interaction


def classify(text: str) -> Interaction:
    text = text.lower().replace("’", "'")
    if re.search(r"\b(kill you|hurt you|attack you)\b", text):
        return Interaction("threat", .75)
    if re.search(r"\b(fuck you|shut (?:the fuck )?up|idiot|stupid|asshole|nigg(?:a|er))\b", text):
        return Interaction("insult", .72)
    if re.search(r"\b(thank(?:s| you)?|please|respect you|appreciate you|sorry|helped)\b", text):
        return Interaction("kindness", .55)
    return Interaction("neutral")
