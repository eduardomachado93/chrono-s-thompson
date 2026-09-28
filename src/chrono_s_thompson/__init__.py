import sys
from pathlib import Path

def main() -> None:
    _root = Path(__file__).resolve().parent.parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

    from src.main import main as run_app
    run_app()

__all__ = ["main"]
