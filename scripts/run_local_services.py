"""Launch the three FastAPI services locally with in-memory fakes.

    python scripts/run_local_services.py

This starts memory (8000), rag (8001), and model gateway (8002). Each service
uses its default local provider (fake memory / in-memory vectors / fake router)
unless overridden with environment variables (see README).
"""

from __future__ import annotations

import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> int:
    commands = [
        ["python", "-m", "uvicorn", "services.memory.main:app", "--port", "8000"],
        ["python", "-m", "uvicorn", "services.rag.main:app", "--port", "8001"],
        ["python", "-m", "uvicorn", "services.model_gateway.main:app", "--port", "8002"],
    ]
    processes = [subprocess.Popen(cmd) for cmd in commands]
    try:
        print("Services started: memory=:8000 rag=:8001 model-gateway=:8002 (Ctrl-C to stop)")
        for process in processes:
            process.wait()
    except KeyboardInterrupt:
        for process in processes:
            process.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
