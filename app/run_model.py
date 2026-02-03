import os
import sys
import time

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from keras import layers

from prediction import TrafficModel
from prediction import retrieve_csv, prepare_targets

# TODO -- Add normalization
# TODO -- Get file from params.conf and change other run / maybe create headers in run_network and remove header_false and columns_name
csv_path = "data/dataset.csv"
sequence_length = 5
training_slice = 0.8

if __name__ == "__main__":
    print("Retrieving data and preparing targets.")
    data = retrieve_csv(csv_path)
    predict, target = prepare_targets(data, sequence_length)

    print(
        f"Splitting data: training->{int(training_slice*100)}% - validation->{int((100-training_slice*100))}%."
    )
    split = int(len(predict) * 0.8)
    x_train, x_val = predict[:split], predict[split:]
    y_train, y_val = target[:split], target[split:]

    input = layers.Input(shape=(sequence_length, 12))
    model = TrafficModel()
    output = model(input)
    model.summary()

    model.compile(optimizer="adam", loss="mse", metrics=["mae"])

    print("Training starting.")
    training_time = time.time()
    model.fit(
        x_train, y_train, validation_data=(x_val, y_val), epochs=100, batch_size=32
    )
    print(f"Training ended succesfully in {int(time.time()-training_time)}s")
