import os
import joblib
import numpy as np
import pandas as pd

from tensorflow.keras.models import load_model
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

# =============================
# CONFIG
# =============================

FEATURES = ["AccX", "AccY", "AccZ", "GyrX", "GyrY", "GyrZ"]
LABEL_COL = "Label"

WINDOW_SIZE = 50
STEP_SIZE = 25          # ใช้ 25 เพื่อให้เหมือน train ที่ overlap 50%
THRESHOLD = 0.7

MODEL_PATH = "LSTM_fall_detection_model_subjectwise.keras"
IMPUTER_PATH = "LSTM_imputer_subjectwise.pkl"
SCALER_PATH = "LSTM_scaler_subjectwise.pkl"

TEST_FILE = r"D:\THESIS\DATASET\Taskdev\Task\T30\S06T30R01.csv"


# =============================
# TERMINAL COLOR
# =============================

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


# =============================
# CREATE SEQUENCES
# =============================

def create_sequences_for_prediction(df):
    X_seq = []
    y_true = []
    start_indices = []
    end_indices = []

    X = df[FEATURES].values
    y = df[LABEL_COL].values

    for start in range(0, len(X) - WINDOW_SIZE + 1, STEP_SIZE):
        end = start + WINDOW_SIZE

        X_seq.append(X[start:end])
        y_true.append(y[end - 1])  # ใช้ label ของ sample สุดท้ายเหมือนตอน train
        start_indices.append(start)
        end_indices.append(end - 1)

    return (
        np.array(X_seq),
        np.array(y_true),
        np.array(start_indices),
        np.array(end_indices)
    )


# =============================
# MAIN
# =============================

def main():
    print("Loading model...")
    model = load_model(MODEL_PATH)
    imputer = joblib.load(IMPUTER_PATH)
    scaler = joblib.load(SCALER_PATH)

    print("Reading test file...")

    if not os.path.exists(TEST_FILE):
        raise FileNotFoundError(f"Test file not found: {TEST_FILE}")

    df = pd.read_csv(TEST_FILE)

    missing_cols = [col for col in FEATURES + [LABEL_COL] if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns in CSV: {missing_cols}")

    df = df.dropna(subset=FEATURES + [LABEL_COL])
    df[LABEL_COL] = df[LABEL_COL].astype(int)

    X, y_true, start_indices, end_indices = create_sequences_for_prediction(df)

    if len(X) == 0:
        print("Not enough data. Need at least 50 samples.")
        return

    print("Input shape:", X.shape)
    print("Total windows:", len(X))

    num_features = X.shape[2]

    X_2d = X.reshape(-1, num_features)
    X_2d = imputer.transform(X_2d)
    X_2d = scaler.transform(X_2d)
    X = X_2d.reshape(X.shape)

    print("\nPredicting...")

    y_prob = model.predict(X, verbose=0)

    y_pred = []

    print("\n========== Prediction Result ==========\n")

    for i in range(len(y_prob)):
        nonfall_prob = y_prob[i][0]
        fall_prob = y_prob[i][1]

        if fall_prob >= THRESHOLD:
            pred_label = 1
            pred_text = "Fall"
        else:
            pred_label = 0
            pred_text = "Non-Fall"

        true_label = int(y_true[i])
        true_text = "Fall" if true_label == 1 else "Non-Fall"

        y_pred.append(pred_label)

        correct = pred_label == true_label

        color = GREEN if correct else RED
        status = "CORRECT" if correct else "WRONG"

        print(color + "--------------------------------------" + RESET)
        print(color + f"Window {i + 1}" + RESET)
        print(f"Sample Range        : {start_indices[i]} - {end_indices[i]}")
        print(f"Ground Truth        : {true_text} ({true_label})")
        print(f"Prediction          : {pred_text} ({pred_label})")
        print(f"Non-Fall Probability: {nonfall_prob:.4f}")
        print(f"Fall Probability    : {fall_prob:.4f}")
        print(color + f"Result              : {status}" + RESET)

    y_pred = np.array(y_pred)

    accuracy = accuracy_score(y_true, y_pred)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])

    print("\n========== Summary ==========")
    print(f"Total windows : {len(y_true)}")
    print(f"Accuracy      : {accuracy:.4f}")

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

    fall_true_count = np.sum(y_true == 1)
    fall_pred_count = np.sum(y_pred == 1)

    print("\n========== Fall Summary ==========")
    print(f"Ground Truth Fall windows : {fall_true_count}")
    print(f"Predicted Fall windows    : {fall_pred_count}")

    if fall_pred_count > 0:
        print(RED + "\nFinal Decision: Fall detected" + RESET)
    else:
        print(GREEN + "\nFinal Decision: Non-Fall" + RESET)


if __name__ == "__main__":
    main()
