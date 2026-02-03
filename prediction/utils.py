import pandas as pd
import numpy as np


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

    return data


def prepare_targets(data, sequence_length):
    """Creates the x (input sequence) and the y (corresponding target) for the model.
    The function also normalizes the data.

    Args:
        data : Parsed csv file.
        sequence_length (int): Length of the sequence.
    """

    x, y = [], []
    data = data.drop(columns=["timestamp"])
    data = data.to_numpy()
    for i in range(len(data) - sequence_length):
        x.append(data[i : i + sequence_length])
        y.append(data[i + sequence_length])

    return np.array(x, dtype=np.float32), np.array(y, dtype=np.float32)
