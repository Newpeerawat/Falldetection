import os
import re
import json
import joblib
import time
import logging

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy import stats

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
    classification_report
)

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Input, LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.optimizers import Adam


# =========================================================
# CONFIG
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

FEATURES = [
    "AccX",
    "AccY",
    "AccZ",
    "GyrX",
    "GyrY",
    "GyrZ"
]

LABEL_COL = "Label"

MAIN_FOLDER = "D:/THESIS/DATASET/Taskdev/Task"

WINDOW_SIZE = 50
OVERLAP = 0.5
TEST_SIZE = 0.2

EPOCHS = 25
BATCH_SIZE = 128
LEARNING_RATE = 0.0005

MODEL_PATH = "LSTM_fall_detection_model_subjectwise.keras"
IMPUTER_PATH = "LSTM_imputer_subjectwise.pkl"
SCALER_PATH = "LSTM_scaler_subjectwise.pkl"

SPLIT_INFO_PATH = "LSTM_subject_split_info.json"
METRICS_PATH = "LSTM_evaluation_metrics.json"

ROC_IMAGE_PATH = "LSTM_ROC_curve.png"
CONFUSION_MATRIX_IMAGE_PATH = "LSTM_confusion_matrix.png"
TRAINING_HISTORY_IMAGE_PATH = "LSTM_training_history.png"


# =========================================================
# FILE AND DATA FUNCTIONS
# =========================================================

def extract_subject_id(file_name):
    """
    Example:
        S06T20R01.csv -> S06
    """
    match = re.search(r"S\d+", file_name)

    if match:
        return match.group(0)

    return "Unknown"


def read_and_combine_data(main_folder):
    """
    Read CSV files from folders T01-T36 and combine them
    into a single DataFrame.
    """
    data_list = []

    for task_id in range(1, 37):
        folder_name = f"T{task_id:02d}"
        folder_path = os.path.join(main_folder, folder_name)

        if not os.path.exists(folder_path):
            logging.warning(
                f"Folder {folder_name} does not exist. Skipping."
            )
            continue

        for file_name in os.listdir(folder_path):
            if not file_name.lower().endswith(".csv"):
                continue

            file_path = os.path.join(folder_path, file_name)

            try:
                df = pd.read_csv(file_path)

                missing_features = [
                    column
                    for column in FEATURES + [LABEL_COL]
                    if column not in df.columns
                ]

                if missing_features:
                    logging.warning(
                        f"Skipping {file_name}. "
                        f"Missing columns: {missing_features}"
                    )
                    continue

                df["SubjectID"] = extract_subject_id(file_name)
                df["TaskID"] = folder_name
                df["FileName"] = file_name

                data_list.append(df)

            except Exception as error:
                logging.error(
                    f"Error reading {file_path}: {error}"
                )

    if not data_list:
        raise ValueError(
            "No valid CSV files were found."
        )

    combined_data = pd.concat(
        data_list,
        ignore_index=True
    )

    return combined_data


def clean_data(data):
    """
    Clean input data:
    1. Convert features and labels to numeric
    2. Remove missing values
    3. Keep labels 0 and 1
    4. Remove outliers using Z-score
    """
    data = data.copy()

    required_columns = FEATURES + [
        LABEL_COL,
        "SubjectID",
        "TaskID",
        "FileName"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    for feature in FEATURES:
        data[feature] = pd.to_numeric(
            data[feature],
            errors="coerce"
        )

    data[LABEL_COL] = pd.to_numeric(
        data[LABEL_COL],
        errors="coerce"
    )

    data = data.dropna(
        subset=FEATURES + [
            LABEL_COL,
            "SubjectID"
        ]
    )

    data[LABEL_COL] = data[LABEL_COL].astype(int)

    data = data[
        data[LABEL_COL].isin([0, 1])
    ]

    if data.empty:
        raise ValueError(
            "No data remains after removing invalid values."
        )

    z_scores = np.abs(
        stats.zscore(
            data[FEATURES],
            nan_policy="omit"
        )
    )

    if z_scores.ndim == 1:
        valid_rows = z_scores < 3.5
    else:
        valid_rows = (z_scores < 3.5).all(axis=1)

    data = data[valid_rows]

    if data.empty:
        raise ValueError(
            "No data remains after outlier removal."
        )

    return data.reset_index(drop=True)


# =========================================================
# SEQUENCE CREATION
# =========================================================

def create_sequences(
    data,
    window_size=50,
    overlap=0.5
):
    """
    Create time-series sequences.

    Window size:
        50 samples

    Overlap:
        50%

    Labeling strategy:
        Label from the final sample of each window
    """
    step_size = int(
        window_size * (1 - overlap)
    )

    if step_size < 1:
        step_size = 1

    X_sequences = []
    y_sequences = []
    subject_sequences = []

    group_columns = [
        "SubjectID",
        "TaskID",
        "FileName"
    ]

    for _, group in data.groupby(
        group_columns,
        sort=False
    ):
        group = group.reset_index(drop=True)

        X_group = group[FEATURES].values
        y_group = group[LABEL_COL].values

        subject_id = group["SubjectID"].iloc[0]

        if len(X_group) < window_size:
            continue

        for start in range(
            0,
            len(X_group) - window_size + 1,
            step_size
        ):
            end = start + window_size

            sequence = X_group[start:end]
            sequence_label = y_group[end - 1]

            X_sequences.append(sequence)
            y_sequences.append(sequence_label)
            subject_sequences.append(subject_id)

    if not X_sequences:
        raise ValueError(
            "No sequences were created. "
            "Check WINDOW_SIZE and the CSV file lengths."
        )

    return (
        np.asarray(
            X_sequences,
            dtype=np.float32
        ),
        np.asarray(
            y_sequences,
            dtype=np.int32
        ),
        np.asarray(subject_sequences)
    )


# =========================================================
# SUBJECT-WISE SPLIT
# =========================================================

def subject_wise_split(X, y, subjects):
    """
    Split data by subject.

    Subjects in the test set do not appear
    in the training set.
    """
    unique_subjects = np.unique(subjects)

    if len(unique_subjects) < 2:
        raise ValueError(
            "At least two subjects are required "
            "for subject-wise splitting."
        )

    train_subjects, test_subjects = train_test_split(
        unique_subjects,
        test_size=TEST_SIZE,
        random_state=42,
        shuffle=True
    )

    train_mask = np.isin(
        subjects,
        train_subjects
    )

    test_mask = np.isin(
        subjects,
        test_subjects
    )

    X_train = X[train_mask]
    X_test = X[test_mask]

    y_train = y[train_mask]
    y_test = y[test_mask]

    if len(X_train) == 0:
        raise ValueError(
            "Training set is empty."
        )

    if len(X_test) == 0:
        raise ValueError(
            "Test set is empty."
        )

    return (
        X_train,
        X_test,
        y_train,
        y_test,
        train_subjects,
        test_subjects
    )


# =========================================================
# PREPROCESSING
# =========================================================

def fit_preprocessing(X_train, X_test):
    """
    Fit imputer and scaler using only training data
    to prevent data leakage.
    """
    number_of_features = X_train.shape[2]

    train_original_shape = X_train.shape
    test_original_shape = X_test.shape

    X_train_2d = X_train.reshape(
        -1,
        number_of_features
    )

    X_test_2d = X_test.reshape(
        -1,
        number_of_features
    )

    imputer = SimpleImputer(
        strategy="mean"
    )

    scaler = StandardScaler()

    X_train_2d = imputer.fit_transform(
        X_train_2d
    )

    X_test_2d = imputer.transform(
        X_test_2d
    )

    X_train_2d = scaler.fit_transform(
        X_train_2d
    )

    X_test_2d = scaler.transform(
        X_test_2d
    )

    X_train = X_train_2d.reshape(
        train_original_shape
    ).astype(np.float32)

    X_test = X_test_2d.reshape(
        test_original_shape
    ).astype(np.float32)

    return (
        X_train,
        X_test,
        imputer,
        scaler
    )


# =========================================================
# LSTM MODEL
# =========================================================

def build_lstm_model():
    model = Sequential([
        Input(
            shape=(
                WINDOW_SIZE,
                len(FEATURES)
            )
        ),

        LSTM(
            units=64,
            return_sequences=True
        ),

        Dropout(0.2),

        LSTM(
            units=32
        ),

        Dropout(0.2),

        Dense(
            units=32,
            activation="relu"
        ),

        Dense(
            units=2,
            activation="softmax"
        )
    ])

    model.compile(
        optimizer=Adam(
            learning_rate=LEARNING_RATE
        ),
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )

    return model


# =========================================================
# GRAPH FUNCTIONS
# =========================================================

def save_roc_curve(
    y_true,
    fall_probabilities,
    roc_auc,
    save_path
):
    """
    Save ROC curve as PNG.
    """
    false_positive_rate, true_positive_rate, thresholds = roc_curve(
        y_true,
        fall_probabilities,
        pos_label=1
    )

    plt.figure(figsize=(7, 6))

    plt.plot(
        false_positive_rate,
        true_positive_rate,
        linewidth=2,
        label=f"LSTM ROC Curve (AUC = {roc_auc:.4f})"
    )

    plt.plot(
        [0, 1],
        [0, 1],
        linestyle="--",
        linewidth=1.5,
        label="Random Classifier"
    )

    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve - LSTM Fall Detection")

    plt.xlim(0.0, 1.0)
    plt.ylim(0.0, 1.05)

    plt.grid(alpha=0.3)
    plt.legend(loc="lower right")
    plt.tight_layout()

    plt.savefig(
        save_path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    return (
        false_positive_rate,
        true_positive_rate,
        thresholds
    )


def save_confusion_matrix_image(
    confusion_matrix_values,
    save_path
):
    """
    Save confusion matrix as PNG.
    """
    class_names = [
        "Non-Fall",
        "Fall"
    ]

    plt.figure(figsize=(6, 5))

    image = plt.imshow(
        confusion_matrix_values,
        interpolation="nearest"
    )

    plt.title(
        "Confusion Matrix - LSTM Fall Detection"
    )

    plt.colorbar(image)

    tick_positions = np.arange(
        len(class_names)
    )

    plt.xticks(
        tick_positions,
        class_names
    )

    plt.yticks(
        tick_positions,
        class_names
    )

    threshold = (
        confusion_matrix_values.max() / 2.0
        if confusion_matrix_values.max() > 0
        else 0
    )

    for row in range(
        confusion_matrix_values.shape[0]
    ):
        for column in range(
            confusion_matrix_values.shape[1]
        ):
            value = confusion_matrix_values[
                row,
                column
            ]

            text_color = (
                "white"
                if value > threshold
                else "black"
            )

            plt.text(
                column,
                row,
                str(value),
                horizontalalignment="center",
                verticalalignment="center",
                color=text_color,
                fontsize=14
            )

    plt.ylabel("True Label")
    plt.xlabel("Predicted Label")

    plt.tight_layout()

    plt.savefig(
        save_path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


def save_training_history(
    history,
    save_path
):
    """
    Save training and validation accuracy/loss.
    """
    epochs = range(
        1,
        len(history.history["loss"]) + 1
    )

    figure, axes = plt.subplots(
        1,
        2,
        figsize=(12, 5)
    )

    axes[0].plot(
        epochs,
        history.history["accuracy"],
        label="Training Accuracy"
    )

    axes[0].plot(
        epochs,
        history.history["val_accuracy"],
        label="Validation Accuracy"
    )

    axes[0].set_title(
        "Training and Validation Accuracy"
    )

    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Accuracy")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    axes[1].plot(
        epochs,
        history.history["loss"],
        label="Training Loss"
    )

    axes[1].plot(
        epochs,
        history.history["val_loss"],
        label="Validation Loss"
    )

    axes[1].set_title(
        "Training and Validation Loss"
    )

    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Loss")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    figure.tight_layout()

    figure.savefig(
        save_path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close(figure)


# =========================================================
# MODEL EVALUATION
# =========================================================

def evaluate_model(
    model,
    X_test,
    y_test,
    y_test_categorical
):
    number_of_test_windows = len(X_test)

    if number_of_test_windows == 0:
        raise ValueError(
            "Test set is empty."
        )

    print("\nWarming up model...")

    model.predict(
        X_test[:1],
        verbose=0
    )

    # -----------------------------------------------------
    # Evaluation time
    # -----------------------------------------------------

    evaluation_start_time = time.perf_counter()

    test_loss, test_accuracy = model.evaluate(
        X_test,
        y_test_categorical,
        batch_size=BATCH_SIZE,
        verbose=0
    )

    evaluation_time_seconds = (
        time.perf_counter()
        - evaluation_start_time
    )

    evaluation_time_per_window_seconds = (
        evaluation_time_seconds
        / number_of_test_windows
    )

    evaluation_time_per_window_ms = (
        evaluation_time_per_window_seconds
        * 1000
    )

    # -----------------------------------------------------
    # Prediction time
    # -----------------------------------------------------

    prediction_start_time = time.perf_counter()

    y_probability = model.predict(
        X_test,
        batch_size=BATCH_SIZE,
        verbose=0
    )

    prediction_time_seconds = (
        time.perf_counter()
        - prediction_start_time
    )

    prediction_time_per_window_seconds = (
        prediction_time_seconds
        / number_of_test_windows
    )

    prediction_time_per_window_ms = (
        prediction_time_per_window_seconds
        * 1000
    )

    prediction_throughput = (
        number_of_test_windows
        / prediction_time_seconds
        if prediction_time_seconds > 0
        else 0
    )

    # -----------------------------------------------------
    # Prediction result
    # -----------------------------------------------------

    y_predicted = np.argmax(
        y_probability,
        axis=1
    )

    fall_probabilities = y_probability[:, 1]

    # -----------------------------------------------------
    # Metrics
    # -----------------------------------------------------

    accuracy = accuracy_score(
        y_test,
        y_predicted
    )

    precision = precision_score(
        y_test,
        y_predicted,
        zero_division=0
    )

    recall = recall_score(
        y_test,
        y_predicted,
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        y_predicted,
        zero_division=0
    )

    cm = confusion_matrix(
        y_test,
        y_predicted,
        labels=[0, 1]
    )

    true_negative, false_positive, false_negative, true_positive = cm.ravel()

    specificity = (
        true_negative
        / (true_negative + false_positive)
        if (true_negative + false_positive) > 0
        else 0
    )

    sensitivity = recall

    false_alarm_rate = (
        false_positive
        / (false_positive + true_negative)
        if (false_positive + true_negative) > 0
        else 0
    )

    # -----------------------------------------------------
    # Confusion matrix image
    # -----------------------------------------------------

    save_confusion_matrix_image(
        confusion_matrix_values=cm,
        save_path=CONFUSION_MATRIX_IMAGE_PATH
    )

    # -----------------------------------------------------
    # ROC Curve
    # -----------------------------------------------------

    unique_test_labels = np.unique(
        y_test
    )

    if len(unique_test_labels) == 2:
        roc_auc = roc_auc_score(
            y_test,
            fall_probabilities
        )

        (
            false_positive_rate,
            true_positive_rate,
            roc_thresholds
        ) = save_roc_curve(
            y_true=y_test,
            fall_probabilities=fall_probabilities,
            roc_auc=roc_auc,
            save_path=ROC_IMAGE_PATH
        )

        roc_curve_created = True

    else:
        roc_auc = None
        false_positive_rate = np.array([])
        true_positive_rate = np.array([])
        roc_thresholds = np.array([])
        roc_curve_created = False

        print(
            "Warning: ROC curve could not be created "
            "because the test set contains only one class."
        )

    # -----------------------------------------------------
    # Terminal output
    # -----------------------------------------------------

    print("\n========== Confusion Matrix ==========")
    print(cm)

    print("\nMatrix layout:")
    print("[[TN FP]")
    print(" [FN TP]]")

    print("\n========== Confusion Matrix Values ==========")
    print(f"True Negative  (TN): {true_negative}")
    print(f"False Positive (FP): {false_positive}")
    print(f"False Negative (FN): {false_negative}")
    print(f"True Positive  (TP): {true_positive}")

    print("\n========== Evaluation Metrics ==========")
    print(f"Test Loss             : {test_loss:.6f}")
    print(f"Test Accuracy         : {test_accuracy:.6f}")
    print(f"Accuracy              : {accuracy:.6f}")
    print(f"Precision             : {precision:.6f}")
    print(f"Recall/Sensitivity    : {sensitivity:.6f}")
    print(f"Specificity           : {specificity:.6f}")
    print(f"F1-score              : {f1:.6f}")
    print(f"False Alarm Rate      : {false_alarm_rate:.6f}")

    if roc_auc is not None:
        print(f"ROC-AUC               : {roc_auc:.6f}")

    print("\n========== Execution Time ==========")
    print(
        f"Evaluation Time       : "
        f"{evaluation_time_seconds:.6f} seconds"
    )

    print(
        f"Evaluation per Window : "
        f"{evaluation_time_per_window_ms:.6f} ms"
    )

    print(
        f"Prediction Time       : "
        f"{prediction_time_seconds:.6f} seconds"
    )

    print(
        f"Prediction per Window : "
        f"{prediction_time_per_window_ms:.6f} ms"
    )

    print(
        f"Prediction Throughput : "
        f"{prediction_throughput:.2f} windows/second"
    )

    print(
        f"Number of Test Windows: "
        f"{number_of_test_windows}"
    )

    print("\n========== Classification Report ==========")

    print(
        classification_report(
            y_test,
            y_predicted,
            labels=[0, 1],
            target_names=[
                "Non-Fall",
                "Fall"
            ],
            zero_division=0
        )
    )

    print(
        "Confusion matrix image saved:",
        CONFUSION_MATRIX_IMAGE_PATH
    )

    if roc_curve_created:
        print(
            "ROC curve image saved:",
            ROC_IMAGE_PATH
        )

    metrics = {
        "model_type": "LSTM",

        "number_of_test_windows": int(
            number_of_test_windows
        ),

        "test_loss": float(test_loss),
        "test_accuracy": float(test_accuracy),

        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall_sensitivity": float(sensitivity),
        "specificity": float(specificity),
        "f1_score": float(f1),
        "false_alarm_rate": float(
            false_alarm_rate
        ),

        "roc_auc": (
            float(roc_auc)
            if roc_auc is not None
            else None
        ),

        "evaluation_time_seconds": float(
            evaluation_time_seconds
        ),

        "evaluation_time_per_window_seconds": float(
            evaluation_time_per_window_seconds
        ),

        "evaluation_time_per_window_ms": float(
            evaluation_time_per_window_ms
        ),

        "prediction_time_seconds": float(
            prediction_time_seconds
        ),

        "prediction_time_per_window_seconds": float(
            prediction_time_per_window_seconds
        ),

        "prediction_time_per_window_ms": float(
            prediction_time_per_window_ms
        ),

        "prediction_windows_per_second": float(
            prediction_throughput
        ),

        "confusion_matrix": cm.tolist(),

        "tn": int(true_negative),
        "fp": int(false_positive),
        "fn": int(false_negative),
        "tp": int(true_positive),

        "roc_curve_created": bool(
            roc_curve_created
        ),

        "roc_curve_image": (
            ROC_IMAGE_PATH
            if roc_curve_created
            else None
        ),

        "confusion_matrix_image": (
            CONFUSION_MATRIX_IMAGE_PATH
        ),

        "roc_fpr": false_positive_rate.tolist(),
        "roc_tpr": true_positive_rate.tolist(),
        "roc_thresholds": roc_thresholds.tolist()
    }

    return metrics


# =========================================================
# MAIN
# =========================================================

def main():
    print("Reading data...")

    data = read_and_combine_data(
        MAIN_FOLDER
    )

    print("Raw data shape:", data.shape)

    print("\nCleaning data...")

    data = clean_data(data)

    print("Clean data shape:", data.shape)

    print("\nCreating sequences...")

    X, y, subjects = create_sequences(
        data=data,
        window_size=WINDOW_SIZE,
        overlap=OVERLAP
    )

    print("\n========== Dataset Information ==========")
    print("X shape:", X.shape)
    print("y shape:", y.shape)

    print(
        "Number of subjects:",
        len(np.unique(subjects))
    )

    print(
        "Subjects:",
        np.unique(subjects)
    )

    unique_labels, label_counts = np.unique(
        y,
        return_counts=True
    )

    print("\nSequence label distribution:")

    for label, count in zip(
        unique_labels,
        label_counts
    ):
        label_name = (
            "Fall"
            if label == 1
            else "Non-Fall"
        )

        print(
            f"{label_name} ({label}): {count}"
        )

    print("\nSubject-wise splitting...")

    (
        X_train,
        X_test,
        y_train,
        y_test,
        train_subjects,
        test_subjects
    ) = subject_wise_split(
        X,
        y,
        subjects
    )

    print("\nTrain subjects:", train_subjects)
    print("Test subjects :", test_subjects)

    print("\nX_train shape:", X_train.shape)
    print("X_test shape :", X_test.shape)

    train_unique_labels, train_label_counts = np.unique(
        y_train,
        return_counts=True
    )

    test_unique_labels, test_label_counts = np.unique(
        y_test,
        return_counts=True
    )

    print("\nTraining label distribution:")

    for label, count in zip(
        train_unique_labels,
        train_label_counts
    ):
        print(
            f"Label {label}: {count}"
        )

    print("\nTest label distribution:")

    for label, count in zip(
        test_unique_labels,
        test_label_counts
    ):
        print(
            f"Label {label}: {count}"
        )

    print("\nPreprocessing...")

    (
        X_train,
        X_test,
        imputer,
        scaler
    ) = fit_preprocessing(
        X_train,
        X_test
    )

    y_train_categorical = to_categorical(
        y_train,
        num_classes=2
    )

    y_test_categorical = to_categorical(
        y_test,
        num_classes=2
    )

    print("\nBuilding LSTM model...")

    model = build_lstm_model()

    model.summary()

    early_stopping = EarlyStopping(
        monitor="val_loss",
        patience=3,
        restore_best_weights=True,
        verbose=1
    )

    print("\nTraining LSTM model...")

    training_start_time = time.perf_counter()

    history = model.fit(
        X_train,
        y_train_categorical,
        validation_split=0.2,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=[early_stopping],
        verbose=1
    )

    training_time_seconds = (
        time.perf_counter()
        - training_start_time
    )

    epochs_completed = len(
        history.history["loss"]
    )

    print("\n========== Training Information ==========")

    print(
        f"Training Time  : "
        f"{training_time_seconds:.2f} seconds"
    )

    print(
        f"Epochs Completed: "
        f"{epochs_completed}"
    )

    save_training_history(
        history=history,
        save_path=TRAINING_HISTORY_IMAGE_PATH
    )

    print(
        "Training history saved:",
        TRAINING_HISTORY_IMAGE_PATH
    )

    print("\nEvaluating model on test set...")

    metrics = evaluate_model(
        model=model,
        X_test=X_test,
        y_test=y_test,
        y_test_categorical=y_test_categorical
    )

    metrics["training_time_seconds"] = float(
        training_time_seconds
    )

    metrics["epochs_completed"] = int(
        epochs_completed
    )

    metrics["training_history_image"] = (
        TRAINING_HISTORY_IMAGE_PATH
    )

    metrics["final_training_loss"] = float(
        history.history["loss"][-1]
    )

    metrics["final_training_accuracy"] = float(
        history.history["accuracy"][-1]
    )

    metrics["final_validation_loss"] = float(
        history.history["val_loss"][-1]
    )

    metrics["final_validation_accuracy"] = float(
        history.history["val_accuracy"][-1]
    )

    print("\nSaving model and preprocessing files...")

    model.save(
        MODEL_PATH
    )

    joblib.dump(
        imputer,
        IMPUTER_PATH
    )

    joblib.dump(
        scaler,
        SCALER_PATH
    )

    split_information = {
        "model_type": "LSTM",

        "window_size": WINDOW_SIZE,
        "overlap": OVERLAP,

        "step_size": int(
            WINDOW_SIZE * (1 - OVERLAP)
        ),

        "labeling_strategy": (
            "last sample label in each window"
        ),

        "features": FEATURES,
        "label_column": LABEL_COL,
        "test_size": TEST_SIZE,

        "train_subjects": (
            train_subjects.tolist()
        ),

        "test_subjects": (
            test_subjects.tolist()
        ),

        "model_path": MODEL_PATH,
        "imputer_path": IMPUTER_PATH,
        "scaler_path": SCALER_PATH
    }

    with open(
        SPLIT_INFO_PATH,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            split_information,
            file,
            indent=4,
            ensure_ascii=False
        )

    with open(
        METRICS_PATH,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            metrics,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\n========== Saved Files ==========")
    print("Model              :", MODEL_PATH)
    print("Imputer            :", IMPUTER_PATH)
    print("Scaler             :", SCALER_PATH)
    print("Split information  :", SPLIT_INFO_PATH)
    print("Evaluation metrics :", METRICS_PATH)
    print("ROC curve          :", ROC_IMAGE_PATH)
    print(
        "Confusion matrix   :",
        CONFUSION_MATRIX_IMAGE_PATH
    )
    print(
        "Training history   :",
        TRAINING_HISTORY_IMAGE_PATH
    )

    print("\nDone.")


if __name__ == "__main__":
    main()