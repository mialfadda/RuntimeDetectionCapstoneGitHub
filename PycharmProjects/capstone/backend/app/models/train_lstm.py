import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import EarlyStopping

# ── Config ───────────────────────────────────────────────
DATA_PATH = "data/dataset.csv"
MODEL_DIR = "backend/app/models/saved"
os.makedirs(MODEL_DIR, exist_ok=True)

# ── 1. Load Data ─────────────────────────────────────────
print("[1/5] Loading dataset...")
df = pd.read_csv(DATA_PATH)

# ── 2. Prepare Features ──────────────────────────────────
print("[2/5] Preparing features...")
DROP_COLS = ["url", "type", "label", "scan_date", "domain",
             "web_http_status", "web_is_live", "web_ext_ratio",
             "web_unique_domains", "web_favicon", "web_csp",
             "web_xframe", "web_hsts", "web_xcontent", "web_security_score",
             "web_forms_count", "web_password_fields", "web_hidden_inputs",
             "web_has_login", "web_ssl_valid",
             "https", "abnormal_url"]
X = df.drop(columns=[c for c in DROP_COLS if c in df.columns])
y = df["label"]

X = X.apply(pd.to_numeric, errors="coerce").fillna(0)

# Scale features (important for LSTM)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Save scaler for inference later
joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.pkl"))
print("     Scaler saved.")

# Reshape for LSTM: (samples, timesteps, features)
# We treat each feature as a timestep
X_lstm = X_scaled.reshape((X_scaled.shape[0], X_scaled.shape[1], 1))
y_cat = to_categorical(y, num_classes=4)

print(f"     Input shape: {X_lstm.shape}")

# ── 3. Train/Test Split ──────────────────────────────────
print("[3/5] Splitting data...")
X_train, X_test, y_train, y_test = train_test_split(
    X_lstm, y_cat, test_size=0.2, random_state=42, stratify=y
)
print(f"     Train: {X_train.shape[0]} | Test: {X_test.shape[0]}")

# ── 4. Build LSTM Model ──────────────────────────────────
print("[4/5] Building and training LSTM...")
model = Sequential([
    LSTM(64, input_shape=(X_lstm.shape[1], 1), return_sequences=True),
    Dropout(0.3),
    LSTM(32),
    Dropout(0.3),
    Dense(32, activation="relu"),
    Dense(4, activation="softmax")
])

model.compile(
    optimizer="adam",
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

model.summary()

early_stop = EarlyStopping(
    monitor="val_loss",
    patience=3,
    restore_best_weights=True
)

history = model.fit(
    X_train, y_train,
    epochs=20,
    batch_size=512,
    validation_split=0.1,
    callbacks=[early_stop],
    verbose=1
)

# ── 5. Evaluate & Save ───────────────────────────────────
print("\n[5/5] Evaluating and saving...")
loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
print(f"     Test Accuracy: {accuracy:.4f}")
print(f"     Test Loss: {loss:.4f}")

lstm_path = os.path.join(MODEL_DIR, "lstm_model.keras")
model.save(lstm_path)
print(f"     Saved → {lstm_path}")

print("\n✅ LSTM trained and saved successfully!")