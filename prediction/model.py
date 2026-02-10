import tensorflow as tf
from keras import layers


class TrafficModel(tf.keras.Model):
    """LSTM model for network traffic prediction."""

    def __init__(self):
        """Defines the structure of the layers."""
        super().__init__()
        self.lstm1 = layers.LSTM(64, return_sequences=True)
        self.lstm2 = layers.LSTM(32)
        self.dense1 = layers.Dense(12)

    def call(self, input):
        """Forward pass of the model."""
        x = self.lstm1(input)
        x = self.lstm2(x)
        return self.dense1(x)
