import os
import time
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from tensorflow.keras.models import load_model

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    roc_curve,
    roc_auc_score,
    ConfusionMatrixDisplay
)

# =============================
# CONFIG
# =============================

FEATURES = ["AccX", "AccY", "AccZ", "GyrX", "GyrY", "GyrZ"]
LABEL_COL = "Label"

WINDOW_SIZE = 50
STEP_SIZE = 25
THRESHOLD = 0.2

MODEL_PATH = "LSTM_fall_detection_model_subjectwise.keras"
IMPUTER_PATH = "LSTM_imputer_subjectwise.pkl"
SCALER_PATH = "LSTM_scaler_subjectwise.pkl"

TEST_FILE = r"D:\THESIS\DATASET\Taskdev\Task\T20\S06T20R01.csv"

# ชื่อไฟล์กราฟที่ต้องการบันทึก
ROC_PLOT_PATH = "LSTM_ROC_curve.png"
CONFUSION_MATRIX_PLOT_PATH = "LSTM_confusion_matrix.png"


# =============================
# CREATE SEQUENCES
# =============================

def create_sequences_for_test(df):
    """
    ตัดข้อมูลเป็น Sliding Windows

    X_seq:
        รูปร่าง (จำนวน window, WINDOW_SIZE, จำนวน features)

    y_true:
        ใช้ Label ของข้อมูลตัวสุดท้ายในแต่ละ Window
    """

    X_seq = []
    y_true = []

    X = df[FEATURES].values
    y = df[LABEL_COL].values

    for start in range(0, len(X) - WINDOW_SIZE + 1, STEP_SIZE):
        end = start + WINDOW_SIZE

        X_seq.append(X[start:end])
        y_true.append(y[end - 1])

    return np.asarray(X_seq, dtype=np.float32), np.asarray(y_true, dtype=int)


# =============================
# PLOT ROC CURVE
# =============================

def plot_roc_curve(y_true, fall_probabilities):
    """
    สร้างกราฟ ROC โดยใช้ Probability ของคลาส Fall
    """

    unique_classes = np.unique(y_true)

    # ROC ต้องมีข้อมูลทั้งคลาส 0 และคลาส 1
    if len(unique_classes) < 2:
        print("\nCannot calculate ROC-AUC.")
        print(
            "The test file contains only one class:",
            unique_classes.tolist()
        )
        return None

    fpr, tpr, thresholds = roc_curve(
        y_true,
        fall_probabilities,
        pos_label=1
    )

    roc_auc = roc_auc_score(y_true, fall_probabilities)

    plt.figure(figsize=(8, 6))

    plt.plot(
        fpr,
        tpr,
        linewidth=2,
        label=f"LSTM ROC Curve (AUC = {roc_auc:.4f})"
    )

    # เส้นทแยงมุมแทนการสุ่มทำนาย
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
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.grid(alpha=0.3)
    plt.legend(loc="lower right")
    plt.tight_layout()

    plt.savefig(
        ROC_PLOT_PATH,
        dpi=300,
        bbox_inches="tight"
    )

    plt.show()
    plt.close()

    print(f"ROC curve saved to: {ROC_PLOT_PATH}")

    return roc_auc


# =============================
# PLOT CONFUSION MATRIX
# =============================

def plot_confusion_matrix(cm):
    """
    สร้างกราฟ Confusion Matrix
    """

    display = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=["Non-Fall", "Fall"]
    )

    fig, ax = plt.subplots(figsize=(7, 6))

    display.plot(
        ax=ax,
        values_format="d"
    )

    ax.set_title("Confusion Matrix - LSTM Fall Detection")

    plt.tight_layout()

    plt.savefig(
        CONFUSION_MATRIX_PLOT_PATH,
        dpi=300,
        bbox_inches="tight"
    )

    plt.show()
    plt.close()

    print(
        "Confusion matrix saved to:",
        CONFUSION_MATRIX_PLOT_PATH
    )


# =============================
# MAIN
# =============================

def main():
    total_program_start = time.perf_counter()

    # =============================
    # LOAD MODEL AND PREPROCESSORS
    # =============================

    print("Loading LSTM model...")

    loading_start = time.perf_counter()

    model = load_model(MODEL_PATH)
    imputer = joblib.load(IMPUTER_PATH)
    scaler = joblib.load(SCALER_PATH)

    loading_time = time.perf_counter() - loading_start

    print(f"Loading time: {loading_time:.6f} seconds")

    # =============================
    # READ TEST DATA
    # =============================

    print("\nReading test CSV...")

    if not os.path.exists(TEST_FILE):
        raise FileNotFoundError(
            f"Test file not found: {TEST_FILE}"
        )

    data_preparation_start = time.perf_counter()

    df = pd.read_csv(TEST_FILE)

    missing_cols = [
        col
        for col in FEATURES + [LABEL_COL]
        if col not in df.columns
    ]

    if missing_cols:
        raise ValueError(
            f"Missing columns in CSV: {missing_cols}"
        )

    # แปลง Features เป็นตัวเลข
    for feature in FEATURES:
        df[feature] = pd.to_numeric(
            df[feature],
            errors="coerce"
        )

    # แปลง Label เป็นตัวเลข
    df[LABEL_COL] = pd.to_numeric(
        df[LABEL_COL],
        errors="coerce"
    )

    # ลบข้อมูลที่ไม่มี Label
    # ส่วนค่า NaN ของ Features จะให้ Imputer จัดการ
    df = df.dropna(subset=[LABEL_COL]).copy()

    df[LABEL_COL] = df[LABEL_COL].astype(int)

    # ตรวจสอบว่า Label มีเฉพาะ 0 และ 1
    invalid_labels = df.loc[
        ~df[LABEL_COL].isin([0, 1]),
        LABEL_COL
    ].unique()

    if len(invalid_labels) > 0:
        raise ValueError(
            f"Label must contain only 0 and 1. "
            f"Invalid labels: {invalid_labels}"
        )

    # =============================
    # CREATE WINDOWS
    # =============================

    X_test, y_true = create_sequences_for_test(df)

    if len(X_test) == 0:
        print(
            f"Not enough data. "
            f"Need at least {WINDOW_SIZE} samples."
        )
        return

    print("X_test shape:", X_test.shape)
    print("y_true shape:", y_true.shape)

    print("\nClass distribution:")
    print(f"Non-Fall windows: {np.sum(y_true == 0)}")
    print(f"Fall windows    : {np.sum(y_true == 1)}")

    # =============================
    # PREPROCESSING
    # =============================

    number_of_windows = X_test.shape[0]
    number_of_features = X_test.shape[2]

    # เปลี่ยนจาก 3 มิติเป็น 2 มิติ
    # เพื่อให้ใช้ Imputer และ Scaler ได้
    X_2d = X_test.reshape(
        -1,
        number_of_features
    )

    X_2d = imputer.transform(X_2d)
    X_2d = scaler.transform(X_2d)

    # เปลี่ยนกลับเป็นรูปแบบของ LSTM
    X_test = X_2d.reshape(
        number_of_windows,
        WINDOW_SIZE,
        number_of_features
    ).astype(np.float32)

    data_preparation_time = (
        time.perf_counter() - data_preparation_start
    )

    print(
        f"Data preparation time: "
        f"{data_preparation_time:.6f} seconds"
    )

    # =============================
    # MODEL WARM-UP
    # =============================

    # ครั้งแรก TensorFlow อาจใช้เวลาเพิ่มในการเตรียมระบบ
    # จึงทำ Warm-up ก่อนเริ่มจับเวลาจริง
    print("\nWarming up model...")

    _ = model.predict(
        X_test[:1],
        verbose=0
    )

    # =============================
    # PREDICTION TIME
    # =============================

    print("\nPredicting...")

    prediction_start = time.perf_counter()

    y_prob = model.predict(
        X_test,
        verbose=0
    )

    prediction_time = (
        time.perf_counter() - prediction_start
    )

    average_prediction_time = (
        prediction_time / number_of_windows
    )

    average_prediction_time_ms = (
        average_prediction_time * 1000
    )

    windows_per_second = (
        number_of_windows / prediction_time
        if prediction_time > 0
        else 0
    )

    # =============================
    # CHECK MODEL OUTPUT
    # =============================

    print("Model output shape:", y_prob.shape)

    # รองรับโมเดลแบบ Softmax 2 Outputs
    if y_prob.ndim == 2 and y_prob.shape[1] == 2:
        nonfall_probabilities = y_prob[:, 0]
        fall_probabilities = y_prob[:, 1]

    # รองรับโมเดลแบบ Sigmoid 1 Output
    elif (
        y_prob.ndim == 2
        and y_prob.shape[1] == 1
    ):
        fall_probabilities = y_prob[:, 0]
        nonfall_probabilities = 1.0 - fall_probabilities

    elif y_prob.ndim == 1:
        fall_probabilities = y_prob
        nonfall_probabilities = 1.0 - fall_probabilities

    else:
        raise ValueError(
            f"Unsupported model output shape: {y_prob.shape}"
        )

    y_pred = (
        fall_probabilities >= THRESHOLD
    ).astype(int)

    # =============================
    # DISPLAY EACH PREDICTION
    # =============================

    print("\n========== Prediction Result ==========\n")

    for index in range(number_of_windows):
        true_label = int(y_true[index])
        predicted_label = int(y_pred[index])

        nonfall_probability = float(
            nonfall_probabilities[index]
        )

        fall_probability = float(
            fall_probabilities[index]
        )

        true_text = (
            "Fall"
            if true_label == 1
            else "Non-Fall"
        )

        predicted_text = (
            "Fall"
            if predicted_label == 1
            else "Non-Fall"
        )

        status = (
            "CORRECT"
            if predicted_label == true_label
            else "WRONG"
        )

        print(
            f"Window {index + 1}: "
            f"Ground Truth={true_text} | "
            f"Prediction={predicted_text} | "
            f"Non-Fall={nonfall_probability:.6f} | "
            f"Fall={fall_probability:.6f} | "
            f"{status}"
        )

    # =============================
    # EVALUATION TIME
    # =============================

    evaluation_start = time.perf_counter()

    accuracy = accuracy_score(
        y_true,
        y_pred
    )

    precision = precision_score(
        y_true,
        y_pred,
        zero_division=0
    )

    recall = recall_score(
        y_true,
        y_pred,
        zero_division=0
    )

    f1 = f1_score(
        y_true,
        y_pred,
        zero_division=0
    )

    cm = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1]
    )

    report = classification_report(
        y_true,
        y_pred,
        labels=[0, 1],
        target_names=["Non-Fall", "Fall"],
        zero_division=0
    )

    # คำนวณ Specificity จาก Confusion Matrix
    tn, fp, fn, tp = cm.ravel()

    specificity = (
        tn / (tn + fp)
        if (tn + fp) > 0
        else 0.0
    )

    # คำนวณ ROC-AUC
    if len(np.unique(y_true)) >= 2:
        roc_auc = roc_auc_score(
            y_true,
            fall_probabilities
        )
    else:
        roc_auc = None

    evaluation_time = (
        time.perf_counter() - evaluation_start
    )

    total_program_time = (
        time.perf_counter() - total_program_start
    )

    # =============================
    # SUMMARY
    # =============================

    print("\n========== Evaluation Summary ==========")

    print(f"Threshold  : {THRESHOLD:.4f}")
    print(f"Accuracy   : {accuracy:.4f}")
    print(f"Precision  : {precision:.4f}")
    print(f"Recall     : {recall:.4f}")
    print(f"Specificity: {specificity:.4f}")
    print(f"F1-score   : {f1:.4f}")

    if roc_auc is not None:
        print(f"ROC-AUC    : {roc_auc:.4f}")
    else:
        print("ROC-AUC    : Cannot calculate")
        print(
            "Reason     : Test data contains only one class"
        )

    # =============================
    # TIME SUMMARY
    # =============================

    print("\n========== Time Summary ==========")

    print(
        f"Model loading time          : "
        f"{loading_time:.6f} seconds"
    )

    print(
        f"Data preparation time       : "
        f"{data_preparation_time:.6f} seconds"
    )

    print(
        f"Total prediction time       : "
        f"{prediction_time:.6f} seconds"
    )

    print(
        f"Average prediction/window   : "
        f"{average_prediction_time:.6f} seconds"
    )

    print(
        f"Average prediction/window   : "
        f"{average_prediction_time_ms:.3f} ms"
    )

    print(
        f"Prediction throughput       : "
        f"{windows_per_second:.2f} windows/second"
    )

    print(
        f"Evaluation time             : "
        f"{evaluation_time:.6f} seconds"
    )

    print(
        f"Total program time          : "
        f"{total_program_time:.6f} seconds"
    )

    # =============================
    # CONFUSION MATRIX TEXT
    # =============================

    print("\n========== Confusion Matrix ==========")
    print(cm)

    print("\nConfusion Matrix Details:")
    print(f"True Negative  (TN): {tn}")
    print(f"False Positive (FP): {fp}")
    print(f"False Negative (FN): {fn}")
    print(f"True Positive  (TP): {tp}")

    # =============================
    # CLASSIFICATION REPORT
    # =============================

    print("\n========== Classification Report ==========")
    print(report)

    # =============================
    # CREATE GRAPHS
    # =============================

    print("\nGenerating graphs...")

    plot_confusion_matrix(cm)

    plotted_auc = plot_roc_curve(
        y_true,
        fall_probabilities
    )

    print("\n========== Finished ==========")

    if plotted_auc is not None:
        print(f"Final ROC-AUC: {plotted_auc:.4f}")


if __name__ == "__main__":
    main()