"""Resolve the artifact directory for the ensemble.

Inside a Flask request/app context, returns `current_app.config['MODEL_DIR']`.
Outside Flask (CLI scripts, tests, training), falls back to the `MODEL_DIR`
env var, then to the repo-root `models/` directory.
"""
import os


def _repo_root_models() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "..", "..", "models"))


def model_dir() -> str:
    try:
        from flask import current_app, has_app_context
        if has_app_context():
            configured = current_app.config.get("MODEL_DIR")
            if configured:
                return configured if os.path.isabs(configured) else os.path.abspath(configured)
    except ImportError:
        pass
    return os.environ.get("MODEL_DIR") or _repo_root_models()


def artifact(name: str) -> str:
    return os.path.join(model_dir(), name)
