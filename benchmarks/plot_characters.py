"""Reproduce narrow factual checks, not an overall quality score."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
def main():
    reports=[json.loads(p.read_text()) for p in sorted((ROOT/'benchmarks/character-results').glob('*.json'))]
    groups=[('Character facts',{'background','hobby','authored_fact'},6),('Supplied POV identification',{'visible_building','visible_person'},4),('Corrected name',{'corrected_name'},2)]
    fig,axes=plt.subplots(1,3,figsize=(13,4.6),layout='constrained')
    names=['Original Q4_K_M','Calibrated IQ3_M','Calibrated Q4_K_S','TinyNPC student']
    for ax,(title,cases,total) in zip(axes,groups):
        values=[sum(t['target_fact_found'] is True for t in r['turns'] if t['case'] in cases) for r in reports]
        bars=ax.barh(names,values,color=['#a4b3c4']*3+['#127e73'])
        ax.invert_yaxis();ax.set_xlim(0,total+0.8);ax.set_xticks(range(total+1));ax.set_title(title,fontweight='bold')
        for bar,value in zip(bars,values):ax.text(value+0.08,bar.get_y()+bar.get_height()/2,f'{value}/{total}',va='center')
        ax.spines[['top','right']].set_visible(False)
    fig.suptitle('Character + POV checks: did the reply mention the expected fact?',fontsize=15,fontweight='bold')
    fig.supxlabel('Two characters, one run. Keyword matches do not detect invented additions or measure human-like speech.',fontsize=10)
    fig.savefig(ROOT/'docs/images/characters.png',dpi=160)

if __name__=='__main__':main()
