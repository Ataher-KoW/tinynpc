import json
from pathlib import Path
from .gpu_service import GPUDialogueEngine

def create_dialogue_service():
    settings=json.loads(Path(__file__).with_name('config.json').read_text(encoding='utf-8'))
    return GPUDialogueEngine(settings)
