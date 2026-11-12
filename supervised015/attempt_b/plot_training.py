"""Standalone scientific plot of teacher-forced training diagnostics only."""
import json,statistics,os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/liquid-sense-015-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def point(rows):return statistics.mean(r['nll'] for r in rows),100*sum(r['correct_tokens'] for r in rows)/sum(r['tokens'] for r in rows)
def main():
    assert (HERE/'training_complete.json').exists()
    initial=read(HERE/'initial_teacher_forcing.json')
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    for directory,label,color in [(HERE.parent,'A: taxa .01 (interrompida)','#bb4430'),(HERE,'B: taxa .001','#146b8b')]:
        history=read(directory/'learning_curve.json');measurements=[point(initial)]+[point(x['rows']) for x in history];steps=[0]+[x['optimizer_steps'] for x in history]
        for axis,j in zip(axes,[0,1]):axis.plot(steps,[x[j] for x in measurements],'-o',markersize=4,label=label,color=color)
    axes[0].set(title='Perda média por tarefa',ylabel='Entropia cruzada (escala log)');axes[0].set_yscale('log')
    axes[1].set(title='Precisão dos tokens de solução/EOS',ylabel='Tokens corretos (%)',ylim=(0,101))
    for axis in axes:axis.set_xlabel('Atualizações completas do otimizador');axis.grid(alpha=.2);axis.legend(fontsize=8)
    fig.suptitle('Liquid Sense: ajuste às 8 soluções ensinadas; isto não mede generalização',fontsize=11)
    fig.savefig(HERE/'training_curve.svg',metadata={'Date':None,'Description':'Training-only diagnostics; free-generation task scores are reported separately.'})
    plt.close(fig);print('saved training_curve.svg')
if __name__=='__main__':main()
