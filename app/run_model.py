import os
import sys 

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import tensorflow as tf
import keras

from prediction import TrafficModel
from prediction import retrieve_csv, prepare_targets

# TODO -- Get file from params.conf and change other run / maybe create headers in run_network and remove header_false and columns_name
csv_path = "data/dataset.csv"
headers = ["timestamp", "port", "rx_bytes", "tx_bytes", "rx_packets", "tx_packets"]
sequence_length = 5
training_slice = 0.8

if __name__ == "__main__":
    print("Retrieving data and preparing targets.")
    data = retrieve_csv(csv_path, headers)
    predict, target = prepare_targets(data, sequence_length)
    
    print(f"Splitting data, training:{int(training_slice*100)}% - {int((1.0-training_slice)*100)}%.")
    split = int(len(predict) * 0.8)
    x_train, x_val = predict[:split], predict[split:]
    y_train, y_val = target[:split], target[split:]

    input = keras.layers.Input(shape=(5,12))
    model = TrafficModel()
    output = model(input)
    model.summary()

    model.compile(optimizer="adam", loss="mse", metrics=["mae"])

    model.fit(
        x_train, y_train,
        validation_data=(x_val, y_val),
        epochs=30,
        batch_size=32
    )
    print("Training ended succesfully")