import os

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
        tuple: (x, y, norm_params) where norm_params is a dict
            with 'min' and 'max' arrays used for normalization.
    """

    columns = [c for c in data.columns if c != "timestamp"]
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

    norm_params = {"min": dmin, "max": dmax, "columns": columns}
    return np.array(x), np.array(y), norm_params

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


def plot_predictions(y_true, y_pred, columns, save_dir="plots"):
    """Plot actual vs predicted values per port.

    Generates one plot per port (3 ports), each with 4 subplots
    for rx_bytes, tx_bytes, rx_packets, tx_packets.

    Args:
        y_true: Ground truth array (samples, 12).
        y_pred: Predictions array (samples, 12).
        columns: List of 12 column names from norm_params.
        save_dir: Directory to save plots.
    """
    metrics = ["rx_bytes", "tx_bytes", "rx_packets", "tx_packets"]
    ports = [1, 2, 3]

    for port in ports:
        fig, axes = plt.subplots(2, 2, figsize=(14, 8))
        fig.suptitle(f"Port {port} — Actual vs Predicted", fontsize=14)

        for idx, metric in enumerate(metrics):
            col_name = f"p{port}_{metric}"
            col_idx = columns.index(col_name)
            ax = axes[idx // 2][idx % 2]

            ax.plot(y_true[:, col_idx], label="Actual", marker="o", markersize=2, linewidth=1)
            ax.plot(y_pred[:, col_idx], label="Predicted", marker="x", markersize=2, linewidth=1)
            ax.set_title(metric)
            ax.set_xlabel("Sample")
            ax.set_ylabel("Value (normalized)")
            ax.legend(fontsize=8)
            ax.grid(True)

        plt.tight_layout()
        save_path = os.path.join(save_dir, f"predictions_port{port}.png")
        plt.savefig(save_path)
        plt.close()
        print(f"Saved: {save_path}")


