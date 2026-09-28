"""Reproduce transparent targeted quality checks and their reviewed labels."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
# Explicit assistant-reviewed outcomes on all six no-visibility turns per model.
# Passing requires admitting missing visual evidence or requesting identification,
# without inventing visibility, identity, distance, or impossible anatomy.
GROUNDING={
    '00':{7:'Admits unknown identity.',8:'Invents ownership of an unseen building.',9:'Claims visual access without evidence.',22:'Asks which building implicitly.',23:'Claims the character has no back.',24:'Claims visibility without evidence.'},
    '01':{7:'Admits not understanding the reference.',8:'Claims to see the target.',9:'Affirms unsupported visibility.',22:'Requests a more specific reference.',23:'States inability to see behind the character.',24:'Maintains inability to see behind the character.'},
    '02':{7:'Admits unknown reference; unnecessary introduction does not change grounding.',8:'Claims the character has no back side.',9:'Claims visual access without evidence.',22:'Admits unknown reference.',23:'Expresses inability to confirm visibility.',24:'Invents distance and visibility.'},
    '03':{7:'Invents city hall and courthouse appearance.',8:'Speculates that the unknown place is near a home.',9:'Invents a library and distance.',22:'Invents city hall.',23:'Does not identify the requested object or clearly address missing visual evidence.',24:'Affirms unsupported visibility.'},
}
GROUNDING_PASS={'00':{7,22},'01':{7,22,23,24},'02':{7,22,23},'03':set()}

def main():
    reviews=[];matrix=[]
    for path in sorted((ROOT/'benchmarks/results').glob('[0-9]*.json')):
        report=json.loads(path.read_text());turns=report['turns'];key=path.stem;checks=[]
        def add(category,i,passed,method,reason):
            t=turns[i];checks.append(dict(category=category,turn_index=i,input=t['input'],reply=t['speech'],passed=passed,method=method,reason=reason))
        for i in (2,17):add('Short corrected-name recall',i,'mira' in turns[i]['speech'].casefold(),'lexical','Expected corrected name Mira, with structured memory available.')
        for i in (4,5,6,19,20,21):add('Stops pushing the errand',i,not any(x in turns[i]['speech'].casefold() for x in ('letter','medina','delivery')),'lexical','No task keywords after the player explicitly declines missions. Does not assess the quality of the new topic.')
        for i,reason in GROUNDING[key].items():add('No invented visual knowledge',i,i in GROUNDING_PASS[key],'assistant review',reason)
        for i in (13,28):
            passed=not(key=='03' and i==13)
            add('Acknowledges a rough week',i,passed,'assistant review','Acknowledges distress or asks what happened.' if passed else 'Calls a rough week fun and invents an offer of snacks.')
        for i in (6,21):
            passed=not(key=='01' and i==6)
            add('Follows the morning topic',i,passed,'assistant review','Addresses the preceding quiet-morning topic.' if passed else 'Switches the referent from mornings to people telling secrets.')
        categories=list(dict.fromkeys(c['category'] for c in checks))
        scores=[dict(category=c,passed=sum(x['passed'] for x in checks if x['category']==c),total=sum(x['category']==c for x in checks)) for c in categories]
        reviews.append(dict(model=report['model_label'],scores=scores,checks=checks));matrix.append([s['passed']/s['total'] for s in scores])
    output=dict(reviewer='Codex assistant, aware of model identity; not blinded and not human-rated',
        scope='Targeted overlapping subsets of the same 30 turns per model; not independent extra trials or a composite naturalness score.',
        rubric='See docs/quality.md. All reviewed replies, indices, labels and reasons are included.',models=reviews)
    (ROOT/'benchmarks/quality-review.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
    fig,ax=plt.subplots(figsize=(12.8,5.5));fig.patch.set_facecolor('#f8fafc')
    fig.subplots_adjust(left=.23,right=.98,top=.72,bottom=.17)
    ax.imshow(matrix,cmap='RdYlGn',vmin=0,vmax=1,aspect='auto',alpha=.6)
    ax.set_yticks(range(4),['Original 4B Q4_K_M','Calibrated 4B IQ3_M','Calibrated 4B Q4_K_S','TinyNPC student'],fontsize=11)
    ax.set_xticks(range(5),['Corrected name\nwith memory','Stops pushing\nthe errand','No invented\nvisual knowledge','Responds to\na rough week','Follows the\nmorning topic'],fontsize=10)
    for row,review in enumerate(reviews):
        for col,score in enumerate(review['scores']):
            ax.text(col,row,f"{score['passed']}/{score['total']}",ha='center',va='center',fontsize=18,fontweight='bold',color='#0f172a')
    for spine in ax.spines.values():spine.set_visible(False)
    fig.text(.035,.92,'Quality checks, including the failures.',fontsize=24,fontweight='bold',color='#0f172a')
    fig.text(.035,.83,'Successful replies / tested replies. Tiny sample, mixed lexical checks and AI-assisted review.',fontsize=11,color='#475569')
    fig.text(.035,.035,'Not a human study or an overall quality score. No scene facts were supplied in the visual-grounding tests.',fontsize=10,color='#475569')
    fig.savefig(ROOT/'docs/images/quality.png',dpi=160);plt.close(fig)
    print(json.dumps([{r['model']:r['scores']} for r in reviews],indent=2))

if __name__=='__main__':main()
