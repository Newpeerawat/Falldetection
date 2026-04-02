from tensorflow.keras.models import load_model
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from tensorflow.keras.utils import to_categorical
import time  
from trainAcc import create_sequences, preprocess_data, read_and_combine_data

# โหลดโมเดล
model = load_model("fall_detection_model_Acc.keras") 
print("Model loaded successfully!")

#  โหลดข้อมูล
test_folder = "D:/THESIS/DATASET/Task"  
data_test = read_and_combine_data(test_folder)  
data_test_cleaned = preprocess_data(data_test)

# สร้าง sequences สำหรับการทดสอบ
sequence_length = 50  # ใช้ค่าเดียวกับที่ใช้ในเทรน
X_test, y_test = create_sequences(data_test_cleaned, sequence_length)

# เปลี่ยน labels เป็น categorical
y_test_categorical = to_categorical(y_test)

# จับเวลา Evaluation
start_time = time.time()
loss, accuracy = model.evaluate(X_test, y_test_categorical, verbose=1)
end_time = time.time()
evaluation_time = end_time - start_time
print(f"Test Loss: {loss}")
print(f"Test Accuracy: {accuracy}")
print(f"Evaluation Time: {evaluation_time:.2f} seconds")

# จับเวลา prediction
start_time = time.time()
predictions = model.predict(X_test)
end_time = time.time()
prediction_time = end_time - start_time
print(f"Prediction Time: {prediction_time:.2f} seconds")
 
 
y_pred = np.argmax(predictions, axis=1)
y_true = np.argmax(y_test_categorical, axis=1)

#  Classification Report
print("Classification Report:")
print(classification_report(y_true, y_pred))

# Confusion Matrix
cm = confusion_matrix(y_true, y_pred)

plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
plt.title("Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.show()
