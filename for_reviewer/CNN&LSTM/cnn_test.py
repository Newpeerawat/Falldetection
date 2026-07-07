import os
import joblib
import numpy as np
import pandas as pd

from tensorflow.keras.models import load_model
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

# =============================
# CONFIG
# =============================

FEATURES = ["AccX", "AccY", "AccZ", "GyrX", "GyrY", "GyrZ"]
LABEL_COL = "Label"

WINDOW_SIZE = 50
STEP_SIZE = 25
THRESHOLD = 0.7

MODEL_PATH = "CNN_fall_detection_model_subjectwise.keras"
IMPUTER_PATH = "CNN_imputer_subjectwise.pkl"
SCALER_PATH = "CNN_scaler_subjectwise.pkl"

TEST_FILE = r"D:\THESIS\DATASET\Taskdev\Task\T20\S06T20R01.csv"


# =============================
# CREATE SEQUENCES
# =============================

def create_sequences_for_test(df):
    X_seq = []
    y_true = []

    X = df[FEATURES].values
    y = df[LABEL_COL].values

    for start in range(0, len(X) - WINDOW_SIZE + 1, STEP_SIZE):
        end = start + WINDOW_SIZE

        X_seq.append(X[start:end])
        y_true.append(y[end - 1])

    return np.array(X_seq), np.array(y_true)


# =============================
# MAIN
# =============================

def main():
    print("Loading CNN model...")
    model = load_model(MODEL_PATH)
    imputer = joblib.load(IMPUTER_PATH)
    scaler = joblib.load(SCALER_PATH)

    print("Reading test CSV...")

    if not os.path.exists(TEST_FILE):
        raise FileNotFoundError(f"Test file not found: {TEST_FILE}")

    df = pd.read_csv(TEST_FILE)

    missing_cols = [col for col in FEATURES + [LABEL_COL] if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns in CSV: {missing_cols}")

    df = df.dropna(subset=FEATURES + [LABEL_COL])
    df[LABEL_COL] = df[LABEL_COL].astype(int)

    X_test, y_true = create_sequences_for_test(df)

    if len(X_test) == 0:
        print("Not enough data. Need at least 50 samples.")
        return

    print("X_test shape:", X_test.shape)
    print("y_true shape:", y_true.shape)

    num_features = X_test.shape[2]

    X_2d = X_test.reshape(-1, num_features)
    X_2d = imputer.transform(X_2d)
    X_2d = scaler.transform(X_2d)
    X_test = X_2d.reshape(X_test.shape)

    print("\nPredicting...")

    y_prob = model.predict(X_test, verbose=0)

    y_pred = []

    print("\n========== Prediction Result ==========\n")

    for i in range(len(y_prob)):
        nonfall_prob = y_prob[i][0]
        fall_prob = y_prob[i][1]

        pred_label = 1 if fall_prob >= THRESHOLD else 0
        y_pred.append(pred_label)

        true_label = int(y_true[i])

        true_text = "Fall" if true_label == 1 else "Non-Fall"
        pred_text = "Fall" if pred_label == 1 else "Non-Fall"

        status = "CORRECT" if pred_label == true_label else "WRONG"

        print(
            f"Window {i + 1}: "
            f"Ground Truth={true_text} | "
            f"Prediction={pred_text} | "
            f"Non-Fall={nonfall_prob:.4f} | "
            f"Fall={fall_prob:.4f} | "
            f"{status}"
        )

    y_pred = np.array(y_pred)

    acc = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])

    print("\n========== Summary ==========")
    print(f"Accuracy : {acc:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")
    print(f"F1-score : {f1:.4f}")

    print("\n========== Confusion Matrix ==========")
    print(cm)

    print("\n========== Classification Report ==========")
    print(classification_report(
        y_true,
        y_pred,
        labels=[0, 1],
        target_names=["Non-Fall", "Fall"],
        zero_division=0
    ))


if __name__ == "__main__":
    main()