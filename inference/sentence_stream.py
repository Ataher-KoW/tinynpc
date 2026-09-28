"""Expose only complete spoken sentences from an incomplete JSON speech field."""
import json
import re


def speech_prefix(raw):
    match = re.search(r'"speech"\s*:\s*"', raw)
    if not match: return '', False
    start = match.end()-1
    escaped = False
    end = len(raw)
    complete = False
    for index in range(start+1,len(raw)):
        char=raw[index]
        if escaped: escaped=False
        elif char=='\\': escaped=True
        elif char=='"': end=index+1; complete=True; break
    fragment=raw[start:end]
    if complete:
        return json.loads(fragment), True
    # Drop only a trailing incomplete escape; never emit raw JSON escapes.
    for trim in range(min(7,len(fragment))):
        candidate=fragment if trim==0 else fragment[:-trim]
        try:
            value=json.loads(candidate+'"')
            if value and 0xD800 <= ord(value[-1]) <= 0xDBFF: value=value[:-1]
            return value, False
        except (ValueError,IndexError): pass
    return '', False


class SentenceStream:
    def __init__(self, callback): self.callback=callback; self.sent=0
    def feed(self, raw):
        text, complete=speech_prefix(raw)
        remainder=text[self.sent:]
        for match in re.finditer(r'[.!?](?:["\u201d\u2019])?(?=\s)',remainder):
            end=self.sent+match.end()
            sentence=text[self.sent:end].strip()
            if re.search(r'\b(?:Mr|Mrs|Ms|Dr|Prof|St)\.$',sentence): continue
            if sentence: self.callback(sentence)
            self.sent=end
            # Re-scan after advancing the offset on the next feed.
            return self.feed(raw)
        if complete and text[self.sent:].strip():
            self.callback(text[self.sent:].strip());self.sent=len(text)
