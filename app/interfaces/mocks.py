"""Back-compat shim.

`mocks.py` used to host the heuristic pipeline that pretended to be the real
ML stack. The real pipeline now lives in `app.interfaces.pipeline`; this
module re-exports its public surface so existing imports
(`from app.interfaces.mocks import run_pipeline`) keep working.
"""
from app.interfaces.pipeline import (  # noqa: F401
    generate_explanation,
    run_pipeline,
)

__all__ = ["run_pipeline", "generate_explanation"]
