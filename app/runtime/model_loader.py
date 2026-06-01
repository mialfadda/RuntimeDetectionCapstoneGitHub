"""Generic loader that handles all artifact formats used by the ensemble."""
import os


SUPPORTED_FORMATS = (".pkl", ".joblib", ".keras", ".h5")


def load_model(model_path: str):
    """Load a trained model from disk.

    sklearn / XGBoost: `.pkl` or `.joblib` (joblib).
    Keras LSTM: `.keras` or `.h5` (tensorflow.keras.models.load_model).
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")

    ext = os.path.splitext(model_path)[1].lower()

    if ext in (".pkl", ".joblib"):
        import joblib
        model = joblib.load(model_path)
    elif ext in (".keras", ".h5"):
        from tensorflow.keras.models import load_model as keras_load
        model = keras_load(model_path)
    else:
        raise ValueError(
            f"Unsupported model format: {ext}. Expected one of {SUPPORTED_FORMATS}"
        )

    print(f"[ModelLoader] Loaded model from {model_path}")
    return model


def get_model_info(model) -> dict:
    info = {"model_type": type(model).__name__}
    if hasattr(model, "get_params"):
        info["model_params"] = model.get_params()
    elif hasattr(model, "count_params"):
        info["param_count"] = int(model.count_params())
    return info
