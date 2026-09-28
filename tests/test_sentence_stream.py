import json
from inference.sentence_stream import SentenceStream


def test_sentences_emit_before_complete_json_and_never_duplicate():
    seen=[];stream=SentenceStream(seen.append)
    raw=json.dumps({'speech':'Hello there. How are you?'})
    prefix=raw[:raw.index('How')+1]
    stream.feed(prefix)
    assert seen==['Hello there.']
    for index in range(len(prefix),len(raw)+1):stream.feed(raw[:index])
    stream.feed(raw)
    assert seen==['Hello there.','How are you?']


def test_escaped_quotes_unicode_and_abbreviations():
    text='Dr. Lane said "hello". Nice \U0001f600!'
    raw=json.dumps({'speech':text})
    seen=[];stream=SentenceStream(seen.append)
    for end in range(len(raw)+1):stream.feed(raw[:end])
    assert ' '.join(seen)==text
    assert len(seen)==2
