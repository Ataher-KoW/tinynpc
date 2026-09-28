"""Reject model implementation details outside inference."""
import ast
from pathlib import Path


def test_game_code_only_imports_public_inference_api():
    root=Path(__file__).resolve().parents[1]
    for folder in ("core","demo","examples"):
        for path in (root/folder).glob("*.py"):
            tree=ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node,ast.ImportFrom) and node.module:
                    assert not node.module.startswith("inference."), str(path)
                if isinstance(node,ast.Import):
                    assert all(not x.name.startswith(("llama_cpp","transformers")) for x in node.names), str(path)
            lower=path.read_text(encoding="utf-8").lower()
            assert "qwen" not in lower and ".gguf" not in lower and "_llm" not in lower, str(path)
