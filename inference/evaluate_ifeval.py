"""Evaluate raw model instruction following with the official IFEval scorer."""
import argparse
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import time
import urllib.error
from .gpu_service import GPUDialogueEngine
from .setup import sha256

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',required=True);p.add_argument('--label',required=True)
    p.add_argument('--assets',default='data/ifeval');p.add_argument('--output',required=True)
    args=p.parse_args();assets=Path(args.assets).resolve();output=Path(args.output);output.mkdir(parents=True,exist_ok=True)
    sys.path[:0]=[str(assets/'deps'),str(assets/'upstream')]
    import nltk
    from langdetect import DetectorFactory
    from instruction_following_eval import evaluation_lib as official
    nltk.data.path.insert(0,str(assets/'nltk'));DetectorFactory.seed=0
    source=json.loads((assets/'source.json').read_text())
    for name,digest in source['sha256'].items():
        assert hashlib.sha256((assets/'upstream/instruction_following_eval'/name).read_bytes()).hexdigest()==digest
    # Read UTF-8 explicitly on Windows; create the official input objects unchanged.
    inputs=[official.InputExample(**json.loads(line)) for line in (assets/'upstream/instruction_following_eval/data/input_data.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    settings=json.loads(Path(args.config).read_text());settings.update(context_tokens=8192,seed=42)
    metadata=dict(benchmark='IFEval',label=args.label,source=source,examples=len(inputs),context_tokens=8192,max_output_tokens=2048,temperature=0,seed=42,thinking=False,system_prompt=None,mode='Raw model, no NPC prompt, memory, JSON grammar, or reply repair',dependencies={k:importlib.metadata.version(k) for k in ('nltk','langdetect','absl-py','immutabledict')})
    base=Path(__file__).resolve().parent
    metadata['model_sha256']=sha256((base/settings['model_path']).resolve())
    metadata['server_sha256']=sha256((base/settings['server_path']).resolve())
    raw=output/'responses.jsonl';meta=output/'metadata.json'
    if meta.exists() and json.loads(meta.read_text())!=metadata:raise ValueError('Resume settings differ.')
    meta.write_text(json.dumps(metadata,indent=2))
    records=[json.loads(line) for line in raw.read_text().splitlines()] if raw.exists() else []
    assert len({r['key'] for r in records})==len(records)
    completed={r['key']:r for r in records}
    for inp in inputs:
        if inp.key in completed:assert completed[inp.key]['prompt']==inp.prompt
    engine=GPUDialogueEngine(settings)
    try:
        for index,inp in enumerate(inputs):
            if inp.key in completed:continue
            start=time.perf_counter()
            try:
                with engine.open('/v1/chat/completions',dict(messages=[dict(role='user',content=inp.prompt)],stream=False,temperature=0,seed=42,max_tokens=2048,chat_template_kwargs={'enable_thinking':False}),timeout=300) as response:
                    result=json.load(response)
                choice=result['choices'][0];record=dict(key=inp.key,prompt=inp.prompt,response=choice['message']['content'] or '',finish_reason=choice['finish_reason'],usage=result.get('usage'),seconds=time.perf_counter()-start)
            except urllib.error.HTTPError as exc:
                message=exc.read().decode('utf-8',errors='replace')
                if exc.code!=500 or 'does not match the expected peg-native format' not in message:raise
                # A generated-output parse failure is retained as an empty failed
                # answer, never silently omitted or retried for a better score.
                record=dict(key=inp.key,prompt=inp.prompt,response='',finish_reason='server_output_parse_error',error=message,seconds=time.perf_counter()-start)
            with raw.open('a',encoding='utf-8') as f:f.write(json.dumps(record,ensure_ascii=True)+'\n')
            records.append(record)
            if (index+1)%10==0:print(args.label,index+1,'/',len(inputs),flush=True)
    finally:engine.close()
    assert len(records)==len(inputs)
    mapping={r['prompt']:r['response'] for r in records}
    report=dict(label=args.label,benchmark='IFEval',examples=len(inputs),truncated=sum(r['finish_reason']=='length' for r in records),output_parse_failures=sum(r['finish_reason']=='server_output_parse_error' for r in records),metrics={})
    for kind,fn in [('strict',official.test_instruction_following_strict),('loose',official.test_instruction_following_loose)]:
        outputs=[fn(inp,mapping) for inp in inputs]
        (output/f'{kind}.jsonl').write_text(''.join(json.dumps(asdict(o),ensure_ascii=True)+'\n' for o in outputs),encoding='utf-8')
        count=sum(len(o.follow_instruction_list) for o in outputs)
        report['metrics'][kind]=dict(prompt_accuracy=100*sum(o.follow_all_instructions for o in outputs)/len(outputs),instruction_accuracy=100*sum(sum(o.follow_instruction_list) for o in outputs)/count,prompts=len(outputs),instructions=count)
    (output/'scores.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)

if __name__=='__main__':main()
