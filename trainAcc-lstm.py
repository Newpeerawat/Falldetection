import os
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import matplotlib.pyplot as plt
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.optimizers import Adam
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)

def read_and_combine_data(main_folder):
    data_list = []
    for i in range(1, 37):
        folder_name = f"T{i:02d}"
        folder_path = os.path.join(main_folder, folder_name)
        if not os.path.exists(folder_path):
            logging.warning(f"Folder {folder_name} does not exist. Skipping.")
            continue
        for file_name in os.listdir(folder_path):
            if file_name.endswith(".csv"):
                file_path = os.path.join(folder_path, file_name)
                try:
                    df = pd.read_csv(file_path)
                    data_list.append(df)
                except Exception as e:
                    logging.error(f"Error reading file {file_path}: {e}")
    if not data_list:
        raise ValueError("No valid data files found in the specified directory.")
    return pd.concat(data_list, ignore_index=True)

def preprocess_data(data):
    data_cleaned = data.dropna(subset=['AccX', 'AccY', 'AccZ'])
    
    z_scores = stats.zscore(data_cleaned[['AccX', 'AccY', 'AccZ']])
    outliers = (abs(z_scores) > 3.5)
    data_cleaned = data_cleaned[~outliers.any(axis=1)]
    
    imputer = SimpleImputer(strategy='mean')
    data_cleaned[['AccX', 'AccY', 'AccZ']] = imputer.fit_transform(data_cleaned[['AccX', 'AccY', 'AccZ']])
    
    scaler = StandardScaler()
    data_cleaned[['AccX', 'AccY', 'AccZ']] = scaler.fit_transform(data_cleaned[['AccX', 'AccY', 'AccZ']])
    
    # Drop rows with NaN in Label
    data_cleaned = data_cleaned.dropna(subset=['Label'])
    
    # Convert labels to integers if necessary
    data_cleaned['Label'] = data_cleaned['Label'].astype(int)
    
    return data_cleaned

def create_sequences(data, sequence_length):
    X = data[['AccX', 'AccY', 'AccZ']].values
    y = data['Label'].values
    X_seq, y_seq = [], []
    for i in range(len(X) - sequence_length + 1):
        X_seq.append(X[i:i + sequence_length])
        y_seq.append(y[i + sequence_length - 1])  # Use the last label in the sequence
    return np.array(X_seq), np.array(y_seq)

def build_lstm_model(sequence_length, num_features, num_classes):
    model = Sequential([
        LSTM(64, input_shape=(sequence_length, num_features), return_sequences=True), 
        Dropout(0.2),
        LSTM(16),
        Dropout(0.2),
        Dense(32, activation='relu'),
        Dense(num_classes, activation='softmax')
    ])
    model.compile(optimizer=Adam(learning_rate=0.0005), loss='categorical_crossentropy', metrics=['accuracy'])
    return model


def plot_metrics(history):
    plt.figure(figsize=(12, 4))
    
    # Plot loss
    plt.subplot(1, 2, 1)
    plt.plot(history.history['loss'], label='Training Loss')
    plt.plot(history.history['val_loss'], label='Validation Loss')
    plt.title('Loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    
    # Plot accuracy
    plt.subplot(1, 2, 2)
    plt.plot(history.history['accuracy'], label='Training Accuracy')
    plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
    plt.title('Accuracy')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.legend()
    
    plt.show()
def main():
    main_folder = "D:/THESIS/DATASET/Task"
    sequence_length = 50 
    test_size = 0.2
    epochs = 25
    batch_size = 128 
    model_save_path = "fall_detection_model_Acc.keras"

    logging.info("Reading and combining data...")
    data = read_and_combine_data(main_folder)
    
    logging.info("Preprocessing data...")
    data_cleaned = preprocess_data(data)
    
    logging.info("Creating sequences...")
    X_seq, y_seq = create_sequences(data_cleaned, sequence_length)
    
    logging.info("Encoding labels...")
    y_seq_categorical = to_categorical(y_seq)
    
    logging.info("Splitting data into training and testing sets...")
    X_train, X_val, y_train, y_val = train_test_split(X_seq, y_seq_categorical, test_size=test_size, random_state=42)
    
    logging.info("Building LSTM model...")
    model = build_lstm_model(sequence_length, X_seq.shape[2], y_train.shape[1])
    
    logging.info("Training the model...")
    early_stopping = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)

    # Start timing the training process
    start_time = time.time()

    history = model.fit(X_train, y_train, 
                        epochs=epochs, 
                        batch_size=batch_size, 
                        validation_data=(X_val, y_val), 
                        verbose=1, 
                        callbacks=[early_stopping])

    # End timing the training process
    end_time = time.time()
    training_time = end_time - start_time

    logging.info(f"Training completed in {training_time:.2f} seconds.")
    
    logging.info("Saving the trained model...")

    plot_metrics(history)


    model.save(model_save_path)

if __name__ == "__main__":
    main()




from tensorflow.keras.models import load_model

# Load the model
model = load_model("fall_detection_model_Acc.keras")

# Display the model's architecture
model.summary()
