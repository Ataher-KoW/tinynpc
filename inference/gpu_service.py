"""Owned loopback GPU server. All deployment and prompt details stay here."""
import atexit
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import threading
import time
import urllib.request

ROOT = Path(__file__).resolve().parent


def speech_from_partial(text):
    match = re.search(r'"speech"\s*:\s*', text)
    if not match:
        return None
    try:
        value, _ = json.JSONDecoder().raw_decode(text[match.end():])
    except json.JSONDecodeError:
        return None
    return value.strip() if isinstance(value, str) and value.strip() else None


class GPUDialogueEngine:
    def __init__(self, settings):
        self.settings = settings
        self.lock = threading.Lock()
        self.closed = False
        self.token = secrets.token_urlsafe(32)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        self.url = f'http://127.0.0.1:{port}'
        binary = ROOT / settings['server_path']
        model = (ROOT / settings['model_path']).resolve()
        adapter = (ROOT / settings['adapter_path']).resolve() if settings.get('adapter_path') else None
        for path in (binary, model, *([adapter] if adapter else [])):
            if not path.is_file():
                raise FileNotFoundError(f'Missing inference asset: {path}')
        logdir = ROOT.parent / 'data'
        logdir.mkdir(exist_ok=True)
        self.log = (logdir / 'gpu-server.log').open('w', encoding='utf-8')
        self.process = subprocess.Popen([
            str(binary), '-m', str(model), *(['--lora',str(adapter)] if adapter else []),
            '-ngl', str(settings.get('gpu_layers',99)), '-c', str(settings.get('context_tokens',2048)), '-np', '1', '-b', '512', '-ub', '256',
            '-t', str(settings.get('threads',4)), '--host', '127.0.0.1', '--port', str(port),
            '--api-key', self.token, '--no-webui', '--flash-attn', settings.get('flash_attention','on'),
        ], stdout=self.log, stderr=self.log,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        atexit.register(self.close)
        try:
            deadline = time.monotonic() + 120
            while time.monotonic() < deadline:
                if self.process.poll() is not None:
                    raise RuntimeError('GPU engine exited. See data/gpu-server.log.')
                try:
                    with self.open('/health', timeout=1) as response:
                        if response.status == 200:
                            break
                except OSError:
                    time.sleep(.2)
            else:
                raise RuntimeError('GPU engine startup timed out.')
            # Build the chat template / first generation kernels before advertising
            # readiness. This turn is discarded and never enters NPC memory.
            from .api import DialogueRequest
            self.respond(DialogueRequest('Guide','town resident','calm','Hello.',
                character_traits=('brief','friendly')))
        except BaseException:
            self.close()
            raise

    def open(self, path, payload=None, timeout=30):
        request = urllib.request.Request(self.url + path,
            data=None if payload is None else json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self.token})
        return urllib.request.urlopen(request, timeout=timeout)

    def respond(self, request):
        return self.respond_stream(request)

    def respond_stream(self, request, on_sentence=None):
        from .conversation_policy import conversation_messages, repeats
        messages=conversation_messages(request)
        with self.lock:
            if self.closed:
                raise RuntimeError('Dialogue engine is closed.')
            speech=self._generate(messages,on_sentence=on_sentence) if on_sentence else self._generate(messages)
            if on_sentence is None and repeats(speech,request.history):
                # A single targeted retry is reserved for an actual loop. No
                # canned replies and no extra generation on normal turns.
                repair=[dict(message) for message in messages]
                repair[0]['content']+='\nYour previous reply was repetitive. Answer the latest player message directly with a fresh thought. Do not say: '+speech
                speech=self._generate(repair,temperature=.8)
            return speech

    def _generate(self,messages,temperature=.65,on_sentence=None):
        from .sentence_stream import SentenceStream
        sentences=SentenceStream(on_sentence) if on_sentence else None
        payload=dict(messages=messages,stream=True,temperature=temperature,
            seed=getattr(self,'settings',{}).get('seed',-1),
            chat_template_kwargs={'enable_thinking':False},
            top_p=.9,max_tokens=180,cache_prompt=True,repeat_penalty=1.12,
            response_format={'type':'json_object','schema':{
                'type':'object','properties':{'speech':{'type':'string','minLength':1}},
                'required':['speech'],'additionalProperties':False}})
        # Budget the actual rendered prompt, preserving the system, recent turn,
        # and complete user/assistant pairs. Keep room for the full response.
        if hasattr(self,'settings'):
            messages=[dict(m) for m in messages]
            while True:
                with self.open('/apply-template',dict(messages=messages,add_generation_prompt=True,
                        chat_template_kwargs={'enable_thinking':False})) as rendered:
                    prompt=json.load(rendered)['prompt']
                with self.open('/tokenize',dict(content=prompt,add_special=True)) as encoded:
                    count=len(json.load(encoded)['tokens'])
                if count <= self.settings.get('context_tokens',2048)-220:break
                if len(messages)<=2:raise ValueError('Current NPC context exceeds the available window.')
                del messages[1:3]
            payload['messages']=messages
        result=''
        with self.open('/v1/chat/completions',payload) as response:
            for line in response:
                if not line.startswith(b'data: '):continue
                if line.strip()==b'data: [DONE]':break
                part=json.loads(line[6:])
                if not part.get('choices'):continue
                result+=part['choices'][0].get('delta',{}).get('content') or ''
                if sentences: sentences.feed(result)
                speech=speech_from_partial(result)
                if speech:return speech
        raise ValueError('The model did not return a complete speech field. Try again.')

    def close(self):
        self.closed = True
        process = getattr(self, 'process', None)
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
        if getattr(self, 'log', None):
            self.log.close()
        atexit.unregister(self.close)
