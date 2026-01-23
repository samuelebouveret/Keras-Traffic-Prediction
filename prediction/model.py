import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import tensorflow as tf
from keras import layers


class TrafficModel(tf.keras.Model):
    def __init__(self):
        super().__init__()
        self.lstm1 = layers.LSTM(64, return_sequences=True)
        self.lstm2 = layers.LSTM(32)
        self.dense1 = layers.Dense(1)

    def call(self, input):
        x = self.lstm1(input)
        x = self.lstm2(x)
        return self.dense1(x)


if __name__ == "__main__":

    # TODO -- Don't have data yet so for testing purposes well hardcode epochs, batch size, time window and numbers of features.
    epochs = 50
    batch_size = 32

    capture_window = 10  # Time span in seconds.
    features = 4         # Ideally the numbers of features analyzed (ex. packets, bytes, sender, receiver etc.).

    # TODO -- Define dataset true and predicted data.
    x_input = None
    y_target = None

    model = TrafficModel()
    model.build((None, capture_window, features))
    model.summary()

    model.compile(optimizer="adam", loss="mse", metrics=["mae"])

    # TODO -- Generate a dataset for testing.
    # history = model.fit(
    #     x_input,
    #     y_target,
    #     validation_split=0.2,
    #     epochs=epochs,
    #     batch_size=batch_size
    # )
