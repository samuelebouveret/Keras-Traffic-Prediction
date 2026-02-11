import tensorflow as tf
from keras import layers


class TrafficModel(tf.keras.Model):
    """LSTM model for network traffic prediction."""

    def __init__(self):
        """Defines the structure of the layers."""
        super().__init__()
        self.lstm1 = layers.LSTM(128, return_sequences=True)
        self.dropout1 = layers.Dropout(0.3)
        self.lstm2 = layers.LSTM(64)
        self.dropout2 = layers.Dropout(0.3)
        self.dense1 = layers.Dense(32, activation="relu")
        self.dense_out = layers.Dense(12)

    def call(self, input, training=False):
        """Forward pass of the model."""
        x = self.lstm1(input)
        x = self.dropout1(x, training=training)
        x = self.lstm2(x)
        x = self.dropout2(x, training=training)
        x = self.dense1(x)
        return self.dense_out(x)
