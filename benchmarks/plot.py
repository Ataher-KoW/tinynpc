"""Recreate every chart from the checked-in measured turns. No invented comparisons."""
from pathlib import Path
import json
import statistics
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
COLORS=['#94a3b8','#64748b','#7c83fd','#14b8a6']
LABELS=['Original 4B\nQ4_K_M','Calibrated 4B\nIQ3_M','Calibrated 4B\nQ4_K_S','TinyNPC student\n1.7B Q4_K_M']

def main():
    reports=[json.loads(p.read_text()) for p in sorted((ROOT/'benchmarks/results').glob('[0-9]*.json'))]
    times=[[t['timings']['total_seconds'] for t in r['turns']] for r in reports]
    words=[[len(re.findall(r'\b\w+\b',t['speech'])) for t in r['turns']] for r in reports]
    means=[statistics.mean(x) for x in times];sizes=[r['model_bytes']/1e9 for r in reports]
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,
        'axes.spines.left':False,'axes.spines.bottom':False,'figure.facecolor':'#f8fafc','axes.facecolor':'#f8fafc',
        'text.color':'#0f172a','axes.labelcolor':'#334155','xtick.color':'#475569','ytick.color':'#334155'})
    out=ROOT/'docs/images';out.mkdir(parents=True,exist_ok=True)
    fig,axes=plt.subplots(1,2,figsize=(13,5.8));fig.subplots_adjust(left=.18,right=.96,top=.78,bottom=.2,wspace=.12)
    for ax,values,title,unit,limit in zip(axes,[sizes,means],['Model download size','Mean complete text turn'],['GB','s'],[2.9,.5]):
        bars=ax.barh(range(4),values,color=COLORS,height=.6)
        ax.set_yticks(range(4),LABELS if ax==axes[0] else ['']*4);ax.invert_yaxis();ax.set_xlim(0,limit)
        ax.set_title(title,loc='left',fontweight='bold',pad=18);ax.xaxis.grid(True,alpha=.15);ax.set_axisbelow(True)
        for bar,v in zip(bars,values):ax.text(v+limit*.02,bar.get_y()+bar.get_height()/2,f'{v:.3f} {unit}',va='center',fontweight='bold')
    fig.text(.035,.93,'Small model. Measured speed.',fontsize=25,fontweight='bold')
    fig.text(.035,.855,'RTX 2060 6 GB  |  30 turns per variant  |  Lower is better',fontsize=12,color='#475569')
    fig.text(.035,.075,'One local run. Decimal GB. Text timing includes memory/context and excludes startup, rendering, and speech.',fontsize=10,color='#475569')
    fig.savefig(out/'overview.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(13,5.8));fig.subplots_adjust(left=.08,right=.97,top=.77,bottom=.24,wspace=.25)
    for ax,values,title,label in zip(axes,[times,words],['Every measured response','Reply lengths in the same run'],['Seconds per complete text turn','Words per reply']):
        box=ax.boxplot(values,patch_artist=True,widths=.5,medianprops={'color':'#0f172a','linewidth':2})
        for patch,color in zip(box['boxes'],COLORS):patch.set_facecolor(color);patch.set_alpha(.6)
        for i,(v,c) in enumerate(zip(values,COLORS),1):
            offsets=[((j%7)-3)*.025 for j in range(len(v))]
            ax.scatter([i+x for x in offsets],v,color=c,s=16,alpha=.75,zorder=3)
        ax.set_xticks(range(1,5),LABELS,fontsize=9);ax.set_title(title,loc='left',fontweight='bold',pad=15)
        ax.set_ylabel(label);ax.set_ylim(bottom=0);ax.yaxis.grid(True,alpha=.15);ax.set_axisbelow(True)
    fig.text(.035,.93,'Look beyond the average.',fontsize=25,fontweight='bold')
    fig.text(.035,.855,'All 30 turns shown per variant. Dots are individual replies; boxes show their distribution.',fontsize=11,color='#475569')
    fig.text(.035,.065,'Reply length influences latency. These plots do not measure naturalness or prove better dialogue quality.',fontsize=10,color='#475569')
    fig.savefig(out/'turns.png',dpi=160);plt.close(fig)
    print('Wrote charts from measured turns.')

if __name__=='__main__':main()
