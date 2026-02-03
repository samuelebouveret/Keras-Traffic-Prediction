import pandas as pd
import numpy as np

def retrieve_csv(csv_path, headers):
    data = pd.read_csv(
        csv_path,
        header=None,
        names=headers
    )

    data = data.pivot(
        index="timestamp",
        columns="port",
        values=["rx_bytes", "tx_bytes", "rx_packets", "tx_packets"]
    )
    
    data.columns = [
        f"p{port}_{metric}"
        for metric, port in data.columns
    ]

    data = data.reset_index()

    return data


def prepare_targets(data, sequence_length):
    predict, target = [], []
    data = data.drop(columns=["timestamp"])
    data = data.to_numpy()
    for i in range(len(data) - sequence_length):
        predict.append(data[i:i+sequence_length])
        target.append(data[i+sequence_length])
    return np.array(predict)/255.0, np.array(target)/255.0