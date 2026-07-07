import os
import re
import json
import joblib
import time
import logging
import numpy as np
import pandas as pd
from scipy import stats

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_auc_score, classification_report
)

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    Input, Conv1D, MaxPooling1D, Flatten,
    Dense, Dropout
)
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.optimizers import Adam


# =========================
# CONFIG
# =========================

logging.basicConfig(level=logging.INFO)

FEATURES = ["AccX", "AccY", "AccZ", "GyrX", "GyrY", "GyrZ"]
LABEL_COL = "Label"

MAIN_FOLDER = "D:/THESIS/DATASET/Taskdev/Task"

WINDOW_SIZE = 50
OVERLAP = 0.5
TEST_SIZE = 0.2

EPOCHS = 25
BATCH_SIZE = 128
LEARNING_RATE = 0.0005

MODEL_PATH = "CNN_fall_detection_model_subjectwise.keras"
IMPUTER_PATH = "CNN_imputer_subjectwise.pkl"
SCALER_PATH = "CNN_scaler_subjectwise.pkl"
SPLIT_INFO_PATH = "CNN_subject_split_info.json"
METRICS_PATH = "CNN_evaluation_metrics.json"


# =========================
# FUNCTIONS
# =========================

def extract_subject_id(file_name):
    match = re.search(r"S\d+", file_name)
    return match.group(0) if match else "Unknown"


def read_and_combine_data(main_folder):
    data_list = []

    for task_id in range(1, 37):
        folder_name = f"T{task_id:02d}"
        folder_path = os.path.join(main_folder, folder_name)

        if not os.path.exists(folder_path):
            logging.warning(f"Folder {folder_name} does not exist. Skipping.")
            continue

        for file_name in os.listdir(folder_path):
            if file_name.endswith(".csv"):
                file_path = os.path.join(folder_path, file_name)

                try:
                    df = pd.read_csv(file_path)

                    df["SubjectID"] = extract_subject_id(file_name)
                    df["TaskID"] = folder_name
                    df["FileName"] = file_name

                    data_list.append(df)

                except Exception as e:
                    logging.error(f"Error reading {file_path}: {e}")

    if not data_list:
        raise ValueError("No valid CSV files found.")

    return pd.concat(data_list, ignore_index=True)


def clean_data(data):
    data = data.dropna(subset=FEATURES + [LABEL_COL, "SubjectID"])
    data[LABEL_COL] = data[LABEL_COL].astype(int)

    z_scores = np.abs(stats.zscore(data[FEATURES], nan_policy="omit"))
    data = data[(z_scores < 3.5).all(axis=1)]

    return data.reset_index(drop=True)


def create_sequences(data, window_size=50, overlap=0.5):
    step = int(window_size * (1 - overlap))
    if step < 1:
        step = 1

    X_seq = []
    y_seq = []
    subject_seq = []

    for _, group in data.groupby(["SubjectID", "TaskID", "FileName"]):
        group = group.reset_index(drop=True)

        X = group[FEATURES].values
        y = group[LABEL_COL].values
        subject_id = group["SubjectID"].iloc[0]

        for start in range(0, len(X) - window_size + 1, step):
            end = start + window_size

            X_seq.append(X[start:end])
            y_seq.append(y[end - 1])
            subject_seq.append(subject_id)

    return np.array(X_seq), np.array(y_seq), np.array(subject_seq)


def subject_wise_split(X, y, subjects):
    unique_subjects = np.unique(subjects)

    train_subjects, test_subjects = train_test_split(
        unique_subjects,
        test_size=TEST_SIZE,
        random_state=42,
        shuffle=True
    )

    train_mask = np.isin(subjects, train_subjects)
    test_mask = np.isin(subjects, test_subjects)

    return (
        X[train_mask],
        X[test_mask],
        y[train_mask],
        y[test_mask],
        train_subjects,
        test_subjects
    )


def fit_preprocessing(X_train, X_test):
    num_features = X_train.shape[2]

    X_train_2d = X_train.reshape(-1, num_features)
    X_test_2d = X_test.reshape(-1, num_features)

    imputer = SimpleImputer(strategy="mean")
    scaler = StandardScaler()

    X_train_2d = imputer.fit_transform(X_train_2d)
    X_test_2d = imputer.transform(X_test_2d)

    X_train_2d = scaler.fit_transform(X_train_2d)
    X_test_2d = scaler.transform(X_test_2d)

    X_train = X_train_2d.reshape(X_train.shape)
    X_test = X_test_2d.reshape(X_test.shape)

    return X_train, X_test, imputer, scaler


def build_cnn_model():
    model = Sequential([
        Input(shape=(WINDOW_SIZE, len(FEATURES))),

        Conv1D(filters=64, kernel_size=3, activation="relu", padding="same"),
        MaxPooling1D(pool_size=2),
        Dropout(0.3),

        Conv1D(filters=128, kernel_size=3, activation="relu", padding="same"),
        MaxPooling1D(pool_size=2),
        Dropout(0.3),

        Flatten(),

        Dense(64, activation="relu"),
        Dropout(0.3),

        Dense(2, activation="softmax")
    ])

    model.compile(
        optimizer=Adam(learning_rate=LEARNING_RATE),
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )

    return model


def evaluate_model(model, X_test, y_test, y_test_cat):
    test_loss, test_accuracy = model.evaluate(X_test, y_test_cat, verbose=0)

    y_prob = model.predict(X_test)
    y_pred = np.argmax(y_prob, axis=1)

    acc = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    sensitivity = recall
    false_alarm_rate = fp / (fp + tn) if (fp + tn) > 0 else 0

    try:
        roc_auc = roc_auc_score(y_test, y_prob[:, 1])
    except Exception:
        roc_auc = None

    print("\n========== Confusion Matrix ==========")
    print(cm)

    print("\n========== Evaluation Metrics ==========")
    print(f"Test Loss         : {test_loss:.4f}")
    print(f"Test Accuracy     : {test_accuracy:.4f}")
    print(f"Accuracy          : {acc:.4f}")
    print(f"Precision         : {precision:.4f}")
    print(f"Recall/Sensitivity: {sensitivity:.4f}")
    print(f"Specificity       : {specificity:.4f}")
    print(f"F1-score          : {f1:.4f}")
    print(f"False Alarm Rate  : {false_alarm_rate:.4f}")

    if roc_auc is not None:
        print(f"ROC-AUC           : {roc_auc:.4f}")

    print("\n========== Classification Report ==========")
    print(classification_report(
        y_test,
        y_pred,
        labels=[0, 1],
        target_names=["Non-Fall", "Fall"],
        zero_division=0
    ))

    metrics = {
        "model_type": "CNN-1D",
        "test_loss": float(test_loss),
        "test_accuracy": float(test_accuracy),
        "accuracy": float(acc),
        "precision": float(precision),
        "recall_sensitivity": float(sensitivity),
        "specificity": float(specificity),
        "f1_score": float(f1),
        "false_alarm_rate": float(false_alarm_rate),
        "roc_auc": float(roc_auc) if roc_auc is not None else None,
        "confusion_matrix": cm.tolist(),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp)
    }

    return metrics


# =========================
# MAIN
# =========================

def main():
    print("Reading data...")
    data = read_and_combine_data(MAIN_FOLDER)

    print("Cleaning data...")
    data = clean_data(data)

    print("Creating sequences...")
    X, y, subjects = create_sequences(
        data,
        window_size=WINDOW_SIZE,
        overlap=OVERLAP
    )

    print("\n========== Dataset Info ==========")
    print("X shape:", X.shape)
    print("y shape:", y.shape)
    print("Number of subjects:", len(np.unique(subjects)))
    print("Subjects:", np.unique(subjects))

    print("\nSubject-wise splitting...")
    X_train, X_test, y_train, y_test, train_subjects, test_subjects = subject_wise_split(
        X, y, subjects
    )

    print("Train subjects:", train_subjects)
    print("Test subjects:", test_subjects)

    print("\nPreprocessing...")
    X_train, X_test, imputer, scaler = fit_preprocessing(X_train, X_test)

    y_train_cat = to_categorical(y_train, num_classes=2)
    y_test_cat = to_categorical(y_test, num_classes=2)

    print("\nBuilding CNN model...")
    model = build_cnn_model()
    model.summary()

    early_stopping = EarlyStopping(
        monitor="val_loss",
        patience=3,
        restore_best_weights=True
    )

    print("\nTraining CNN...")
    start_time = time.time()

    model.fit(
        X_train,
        y_train_cat,
        validation_split=0.2,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=[early_stopping],
        verbose=1
    )

    training_time = time.time() - start_time
    print(f"\nTraining time: {training_time:.2f} seconds")

    print("\nEvaluating CNN on test set...")
    metrics = evaluate_model(model, X_test, y_test, y_test_cat)
    metrics["training_time_seconds"] = float(training_time)

    print("\nSaving CNN model and preprocessing files...")
    model.save(MODEL_PATH)
    joblib.dump(imputer, IMPUTER_PATH)
    joblib.dump(scaler, SCALER_PATH)

    split_info = {
        "model_type": "CNN-1D",
        "window_size": WINDOW_SIZE,
        "overlap": OVERLAP,
        "step_size": int(WINDOW_SIZE * (1 - OVERLAP)),
        "labeling_strategy": "last sample label in each window",
        "features": FEATURES,
        "test_size": TEST_SIZE,
        "train_subjects": train_subjects.tolist(),
        "test_subjects": test_subjects.tolist(),
        "model_path": MODEL_PATH,
        "imputer_path": IMPUTER_PATH,
        "scaler_path": SCALER_PATH
    }

    with open(SPLIT_INFO_PATH, "w") as f:
        json.dump(split_info, f, indent=4)

    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=4)

    print("\nDone.")
    print("CNN Model saved:", MODEL_PATH)
    print("Imputer saved:", IMPUTER_PATH)
    print("Scaler saved:", SCALER_PATH)
    print("Split info saved:", SPLIT_INFO_PATH)
    print("Metrics saved:", METRICS_PATH)


if __name__ == "__main__":
    main()