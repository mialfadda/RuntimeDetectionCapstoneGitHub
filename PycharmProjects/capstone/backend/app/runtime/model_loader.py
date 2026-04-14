import os
import joblib


# Supported model types
SUPPORTED_FORMATS = [".pkl", ".joblib"]


def load_model(model_path: str):
    """
    Loads a trained ML model from disk.
    Currently supports sklearn models (Decision Tree, XGBoost, SVM)
    saved as .pkl or .joblib files.
    Will be extended by B2 to support LSTM (.pt, .keras) later.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")

    ext = os.path.splitext(model_path)[1].lower()

    if ext not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported model format: {ext}. Expected one of {SUPPORTED_FORMATS}")

    model = joblib.load(model_path)
    print(f"[ModelLoader] Loaded model from {model_path}")
    return model


def get_model_info(model) -> dict:
    """
    Returns basic metadata about a loaded model.
    """
    return {
        "model_type": type(model).__name__,
        "model_params": model.get_params() if hasattr(model, "get_params") else {},
    }