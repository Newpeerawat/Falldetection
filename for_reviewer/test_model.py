from flask import Flask, request, jsonify
import tensorflow as tf
import numpy as np
import joblib
from collections import deque

app = Flask(__name__)


"""
# แปลงเป็น TFLite
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS, tf.lite.OpsSet.SELECT_TF_OPS]
converter._experimental_lower_tensor_list_ops = False
tflite_model = converter.convert()

# บันทึกไฟล์
with open("fall_detection_model.tflite", "wb") as f:
    f.write(tflite_model)
"""


# โหลดโมเดลที่อัปโหลดมา ACC+GYR with LSTM

MODEL_PATH = "LSTM_fall_detection_model_subjectwise.keras"
IMPUTER_PATH = "LSTM_imputer_subjectwise.pkl"
SCALER_PATH = "LSTM_scaler_subjectwise.pkl"

TIME_STEPS = 50
NUM_FEATURES = 6
THRESHOLD = 0.2

model = tf.keras.models.load_model(MODEL_PATH)
imputer = joblib.load(IMPUTER_PATH)
scaler = joblib.load(SCALER_PATH)


latest_result = "No Fall"
latest_fall_probability = 0.0


@app.route("/predict", methods=["POST"])
def predict():
    global latest_result, latest_fall_probability

    try:
        req = request.get_json(force=True)
        data = req.get("inputs")

        if data is None:
            return jsonify({"error": "Missing inputs"}), 400

        input_sequence = np.array(data, dtype=np.float32)

        if input_sequence.shape != (TIME_STEPS, NUM_FEATURES):
            return jsonify({
                "error": "Invalid input shape",
                "expected": [TIME_STEPS, NUM_FEATURES],
                "received": list(input_sequence.shape)
            }), 400

        sequence_2d = input_sequence.reshape(-1, NUM_FEATURES)

        sequence_2d = imputer.transform(sequence_2d)
        sequence_2d = scaler.transform(sequence_2d)

        input_array = sequence_2d.reshape(1, TIME_STEPS, NUM_FEATURES)

        prediction = model.predict(input_array, verbose=0)

        nonfall_prob = float(prediction[0][0])
        fall_prob = float(prediction[0][1])

        latest_fall_probability = fall_prob
        latest_result = "Fall" if fall_prob >= THRESHOLD else "No Fall"

        print("Prediction:", prediction)
        print("Fall probability:", fall_prob)

        return jsonify({
            "result": latest_result,
            "fall_probability": fall_prob,
            "nonfall_probability": nonfall_prob
        })

    except Exception as e:
        print("ERROR:", repr(e))
        return jsonify({"error": str(e)}), 500


@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "result": latest_result,
        "fall_probability": latest_fall_probability
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)



"""
# โหลดโมเดลที่อัปโหลดมา ACC+GYR with CNN

MODEL_PATH = "CNN_fall_detection_model_subjectwise.keras"
IMPUTER_PATH = "CNN_imputer_subjectwise.pkl"
SCALER_PATH = "CNN_scaler_subjectwise.pkl"

TIME_STEPS = 50
NUM_FEATURES = 6
THRESHOLD = 0.2

model = tf.keras.models.load_model(MODEL_PATH)
imputer = joblib.load(IMPUTER_PATH)
scaler = joblib.load(SCALER_PATH)


latest_result = "No Fall"
latest_fall_probability = 0.0


@app.route("/predict", methods=["POST"])
def predict():
    global latest_result, latest_fall_probability

    try:
        req = request.get_json(force=True)
        data = req.get("inputs")

        if data is None:
            return jsonify({"error": "Missing inputs"}), 400

        input_sequence = np.array(data, dtype=np.float32)

        if input_sequence.shape != (TIME_STEPS, NUM_FEATURES):
            return jsonify({
                "error": "Invalid input shape",
                "expected": [TIME_STEPS, NUM_FEATURES],
                "received": list(input_sequence.shape)
            }), 400

        sequence_2d = input_sequence.reshape(-1, NUM_FEATURES)

        sequence_2d = imputer.transform(sequence_2d)
        sequence_2d = scaler.transform(sequence_2d)

        input_array = sequence_2d.reshape(1, TIME_STEPS, NUM_FEATURES)

        prediction = model.predict(input_array, verbose=0)

        nonfall_prob = float(prediction[0][0])
        fall_prob = float(prediction[0][1])

        latest_fall_probability = fall_prob
        latest_result = "Fall" if fall_prob >= THRESHOLD else "No Fall"

        print("Prediction:", prediction)
        print("Fall probability:", fall_prob)

        return jsonify({
            "result": latest_result,
            "fall_probability": fall_prob,
            "nonfall_probability": nonfall_prob
        })

    except Exception as e:
        print("ERROR:", repr(e))
        return jsonify({"error": str(e)}), 500


@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "result": latest_result,
        "fall_probability": latest_fall_probability
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
"""
