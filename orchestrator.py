# Root shim so tests (and tools) can import `orchestrator` from the project root.
from agent.orchestrator import *  # type: ignore[F401,F403]

if __name__ == "__main__":
    # Allow `python orchestrator.py` from the project root
    from agent.orchestrator import main

    main()
