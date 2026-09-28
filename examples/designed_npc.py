"""Load an authored character and current POV from plain JSON."""
import json
import urllib.request
from pathlib import Path

def main():
    base=Path(__file__).parent
    npc=json.loads((base/'npcs/marcus.json').read_text())
    pov=json.loads((base/'pov/east-gate.json').read_text())
    print('Start python -m core.http_api first. Type /quit to stop.')
    while True:
        text=input('You: ').strip()
        if text=='/quit':break
        if not text:continue
        payload=dict(npc=npc,pov=pov,player_id='example-player',text=text)
        request=urllib.request.Request('http://127.0.0.1:8765/chat',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(request,timeout=60) as response:print(npc['name']+': '+json.load(response)['speech'])

if __name__=='__main__':main()
