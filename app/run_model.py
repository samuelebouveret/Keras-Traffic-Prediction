import os
import sys
import time

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from keras import layers

from oslo_config import cfg

from prediction import TrafficModel
from prediction import retrieve_csv, prepare_targets

CONF = cfg.CONF
cfg.CONF.register_opts(
    [
        cfg.StrOpt("csv_path"),
        cfg.IntOpt("epochs"),
        cfg.IntOpt("batch_size"),
        cfg.IntOpt("sequence_length"),
        cfg.FloatOpt("training_slice"),
    ]
)
CONF(default_config_files=["params.conf"])

if __name__ == "__main__":
    print("Retrieving data and preparing targets.")
    # Preprocessing, not normalized for debugging.
    data = retrieve_csv(CONF.csv_path)
    x, y = prepare_targets(data, CONF.sequence_length)

    print(
        f"Splitting data: training->{int(CONF.training_slice*100)}% - validation->{int((100-CONF.training_slice*100))}%."
    )

    # Split x and why values according to params.conf.
    split = int(len(x) * CONF.training_slice)
    x_train, x_val = x[:split], x[split:]
    y_train, y_val = y[:split], y[split:]

    # Normalize x.
    x_train_flat = x_train.reshape(-1, x_train.shape[-1])
    x_mean = x_train_flat.mean(axis=0)
    x_std  = x_train_flat.std(axis=0)
    x_train= (x_train - x_mean) / x_std
    x_val = (x_val - x_mean) / x_std

    # Normalize y (no need to reshape).
    y_mean = y_train.mean(axis=0)
    y_std  = y_train.std(axis=0)
    y_train = (y_train - y_mean) / y_std
    y_val   = (y_val - y_mean) / y_std

    # Initialize model and input.
    input = layers.Input(shape=(CONF.sequence_length, 12))
    model = TrafficModel()
    output = model(input)
    model.summary()

    model.compile(optimizer="adam", loss="mse", metrics=["mae"])

    print("Training starting.")
    training_time = time.time()
    model.fit(
        x_train,
        y_train,
        validation_data=(x_val, y_val),
        epochs=CONF.epochs,
        batch_size=CONF.batch_size,
    )
    print(f"Training ended succesfully in {int(time.time()-training_time)}s")
