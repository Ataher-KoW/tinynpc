"""Plot saved official IFEval scores from the complete local runs."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    root=Path(__file__).resolve().parents[1]
    reports=[json.loads((root/f'benchmarks/ifeval-results/{name}/scores.json').read_text()) for name in ('original','student')]
    metrics=[('strict','prompt_accuracy','Prompt strict'),('strict','instruction_accuracy','Instruction strict'),('loose','prompt_accuracy','Prompt loose'),('loose','instruction_accuracy','Instruction loose')]
    fig,ax=plt.subplots(figsize=(11,5),layout='constrained')
    for offset,report,color,label in [(-.18,reports[0],'#a4b3c4','Original larger model'),(.18,reports[1],'#127e73','TinyNPC student')]:
        values=[report['metrics'][kind][key] for kind,key,_ in metrics]
        bars=ax.bar([i+offset for i in range(4)],values,width=.36,color=color,label=label)
        ax.bar_label(bars,fmt='%.1f',padding=4)
    ax.set_xticks(range(4),[m[2] for m in metrics]);ax.set_ylim(0,100);ax.set_ylabel('Accuracy (%)');ax.legend()
    ax.set_title('IFEval: instruction-following scores from our local run',fontweight='bold',fontsize=15)
    ax.spines[['top','right']].set_visible(False)
    fig.supxlabel('Full 541 prompts per model | Official scorer | Raw model, thinking disabled | Not a human-like dialogue score',fontsize=9)
    fig.savefig(root/'docs/images/ifeval.png',dpi=160)

if __name__=='__main__':main()
