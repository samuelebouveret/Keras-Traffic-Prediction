import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def retrieve_csv(csv_path):
    """Retrieves the csv data

    Args:
        csv_path (str): Csv full path to the file.

    Returns:
        Formatted data for the model. [timestamp, p1_rx_bytes, p1_tx_bytes, p1_rx_packets, p1_tx_packets, .... p3_tx_packets] shape=(batch, 13)
    """

    data = pd.read_csv(csv_path)

    data = data.pivot(
        index="timestamp",
        columns="port",
        values=["rx_bytes", "tx_bytes", "rx_packets", "tx_packets"],
    )

    data.columns = [f"p{port}_{metric}" for metric, port in data.columns]

    data = data.reset_index()
    data = data.dropna()

    return data


def prepare_targets(data, sequence_length):
    """Creates the x and the y for the model.
    The data is normalized before creating the sequences.

    Args:
        data : Parsed csv file.
        sequence_length (int): Length of the sequence.

    Returns:
        tuple: (x, y) numpy arrays ready for the model.
    """

    data = data.drop(columns=["timestamp"])
    data = data.to_numpy(dtype=np.float32)

    # Min-Max normalization to [0, 1]
    dmin = data.min(axis=0)
    dmax = data.max(axis=0)
    drange = dmax - dmin
    drange[drange == 0] = 1  # avoid division by zero
    data = (data - dmin) / drange

    x, y = [], []
    for i in range(len(data) - sequence_length):
        x.append(data[i : i + sequence_length])
        y.append(data[i + sequence_length])

    return np.array(x), np.array(y)

def plot_loss(history, save_path="plots/loss.png"):
    """Plot training and validation loss."""
    plt.figure(figsize=(8, 5))
    plt.plot(history.history["loss"], label="Train Loss")
    plt.plot(history.history["val_loss"], label="Val Loss")
    plt.xlabel("Epoch")
    plt.ylabel("MSE Loss")
    plt.title("Training vs Validation Loss")
    plt.legend()
    plt.grid(True)
    plt.savefig(save_path)
    plt.close()
    print(f"Saved: {save_path}")


def plot_predictions(y_true, y_pred, save_path="plots/predictions.png"):
    """Plot actual vs predicted values."""
    plt.figure(figsize=(10, 5))
    plt.plot(y_true, label="Actual", marker="o", markersize=3)
    plt.plot(y_pred, label="Predicted", marker="x", markersize=3)
    plt.xlabel("Sample")
    plt.ylabel("Traffic (normalized)")
    plt.title("Actual vs Predicted Traffic")
    plt.legend()
    plt.grid(True)
    plt.savefig(save_path)
    plt.close()
    print(f"Saved: {save_path}")


