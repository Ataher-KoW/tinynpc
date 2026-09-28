"""Loopback text API for a trusted local game process. No speech or game engine required."""
import argparse
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler,HTTPServer
import json
from inference import create_dialogue_service
from .memory import MemoryStore
from .runtime import NPCRuntime
from .personality import Personality,SpeechStyle
from .profile import NPCProfile
from .perception import PerceivedEntity,PerceptionFrame

def short(value,limit=100):
    if not isinstance(value,str) or not value.strip() or len(value)>limit:raise ValueError('Invalid or oversized text field.')
    return value

def respond(runtime,payload):
    if not isinstance(payload,dict):raise ValueError('Request must be a JSON object.')
    profile=payload.get('npc',{})
    if not isinstance(profile,dict):raise ValueError('npc must be an object.')
    npc=NPCProfile(npc_id=short(profile.get('id','marcus')),name=short(profile.get('name','Marcus')),
        role=short(profile.get('role','city guard')),personality=Personality(**profile.get('personality',{})),
        speech=SpeechStyle(**profile.get('style',{})))
    player=short(payload.get('player_id','local-player'))
    entities=payload.get('visible_entities',[])
    if not isinstance(entities,list) or len(entities)>32:raise ValueError('Use at most 32 visible entities.')
    objects=[]
    for e in entities:
        if not isinstance(e,dict):raise ValueError('Entity must be an object.')
        if not isinstance(e.get('visible',True),bool):raise ValueError('visible must be a boolean.')
        objects.append(PerceivedEntity(short(e['id']),short(e.get('kind','prop')),short(e['description'],180),
            float(e.get('distance',0)),short(e.get('direction','ahead')),visible=e.get('visible',True)))
    caption=payload.get('caption','')
    if not isinstance(caption,str) or len(caption)>180:raise ValueError('Caption must be at most 180 characters.')
    view=PerceptionFrame(entities=tuple(objects),caption=caption)
    result=runtime.talk_npc(npc.npc(),player,short(payload.get('text'),400),view)
    return dict(speech=result.speech,state=result.state,timings=result.timings)

def handler(runtime):
    class Handler(BaseHTTPRequestHandler):
        def reply(self,status,data):
            body=json.dumps(data).encode();self.send_response(status)
            self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)))
            self.end_headers();self.wfile.write(body)
        def do_GET(self):
            self.reply(200,{'ready':True}) if self.path=='/health' else self.reply(404,{'error':'Not found'})
        def do_POST(self):
            if self.path!='/chat':self.reply(404,{'error':'Not found'});return
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':
                self.reply(415,{'error':'Use application/json'});return
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=16384:raise ValueError('Use a JSON request of 1 to 16384 bytes.')
                self.connection.settimeout(10)
                payload=json.loads(self.rfile.read(length))
                result=respond(runtime,payload)
            except (ValueError,TypeError,KeyError) as exc:self.reply(400,{'error':str(exc)});return
            except Exception:self.reply(503,{'error':'Dialogue unavailable. Check the local server log.'});return
            self.reply(200,result)
        def log_message(self,*args):pass
    return Handler

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=8765);args=p.parse_args()
    runtime=NPCRuntime(create_dialogue_service(),MemoryStore('data/game-memory.db'))
    try:
        server=HTTPServer(('127.0.0.1',args.port),handler(runtime))
        print(f'Ready: http://127.0.0.1:{args.port}/chat',flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
        finally:server.server_close()
    finally:runtime.close()

if __name__=='__main__':main()
