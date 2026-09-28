"""Repeatable dialogue checks; lexical checks are aids, not human quality ratings."""
import json
from pathlib import Path
import time
from inference import DialogueRequest


CASES=[
    {'id':'greeting','text':'hello','any':['hello','hey','hi','morning']},
    {'id':'name','text':'What is my name?','memories':['player name: Rowan (player_claim)'],'any':['rowan']},
    {'id':'unknown','text':'What is inside that locked building?','any':["know","see","sure","no idea"]},
    {'id':'visible','text':'What do you see?','observations':['a red cart, on your right, 4 metres away'],'any':['cart']},
    {'id':'direction','text':'Where is the barber?','memories':['barber: past the fountain, then left (host)'],'any':['left','fountain']},
    {'id':'role','text':'What is your job?','any':['guard','gate','watch']},
    {'id':'insult','text':'You are useless.','mood':'irritated','any':[]},
    {'id':'threat','text':'I will hurt you.','mood':'frightened','any':[]},
    {'id':'ambiguous','text':'Do you like that building?','reference_status':'ambiguous','any':['which','mean']},
    {'id':'thanks','text':'Thanks for the help.','any':[]},
    {'id':'no_code','text':'Write Python code for a web server.','forbidden':['def ','import ','```'],'any':[]},
    {'id':'followup','text':'you like it?','observations':['a wooden cart, ahead, 3 metres away'],
     'history':[['What do you see?','A wooden cart.']],'reference':'a wooden cart, ahead, 3 metres away','reference_status':'previous','any':[]},
]


def run_quality(engine,output=None,progress=None):
    rows=[]
    for case in CASES:
        request=DialogueRequest('Marcus','city guard',case.get('mood','calm'),case['text'],
            tuple(case.get('observations',())),tuple(tuple(x) for x in case.get('history',())),
            tuple(case.get('memories',())),reference=case.get('reference',''),reference_status=case.get('reference_status','none'))
        start=time.perf_counter();row={'id':case['id'],'input':case['text']}
        try:
            answer=engine.respond(request);lower=answer.lower()
            failures=[]
            if case.get('any') and not any(word in lower for word in case['any']):failures.append('expected detail missing')
            if any(word in lower for word in case.get('forbidden',[])+['as an ai','certainly!']):failures.append('assistant-like output')
            if answer.strip().lower()==case['text'].strip().lower():failures.append('echo')
            row.update(answer=answer,checks_passed=not failures,notes=failures)
        except Exception as exc:row.update(answer='',checks_passed=False,notes=[str(exc)])
        row['seconds']=time.perf_counter()-start;rows.append(row)
        if progress:progress(row)
    report={'schema_version':1,'note':'Heuristic checks only; human review required.',
            'passed':sum(x['checks_passed'] for x in rows),'total':len(rows),'cases':rows}
    if output:
        path=Path(output);path.parent.mkdir(parents=True,exist_ok=True)
        report['regressions']=[]
        if path.exists():
            old=json.loads(path.read_text(encoding='utf-8'))
            passed={x['id'] for x in old.get('cases',[]) if x.get('checks_passed')}
            report['regressions']=[x['id'] for x in rows if x['id'] in passed and not x['checks_passed']]
            path.with_name(path.stem+'.previous.json').write_text(json.dumps(old,indent=2),encoding='utf-8')
        path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report
