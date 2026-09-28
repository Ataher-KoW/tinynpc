"""Benchmark the installed model without changing its configuration."""
import argparse
from pathlib import Path
from inference import create_dialogue_service
from core.conversation_benchmark import run_conversations

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('data/local-benchmark.json'));args=p.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    engine=create_dialogue_service()
    try:
        result=run_conversations(engine,args.output)
        print('Median:',result['median_seconds'],'p95:',result['p95_seconds'],'Flagged:',result['flagged'])
    finally:engine.close()

if __name__=='__main__':main()
