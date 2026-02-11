import os
import sys
import time

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from keras import layers
from keras.callbacks import EarlyStopping

from oslo_config import cfg

from prediction import TrafficModel
from prediction import retrieve_csv, prepare_targets
from prediction.utils import plot_loss, plot_predictions

CONF = cfg.CONF
cfg.CONF.register_opts(
    [
        cfg.StrOpt("csv_path"),
        cfg.StrOpt("model_path", default="models/traffic_model.keras"),
        cfg.IntOpt("epochs"),
        cfg.IntOpt("batch_size"),
        cfg.IntOpt("sequence_length"),
        cfg.FloatOpt("training_slice"),
    ]
)
CONF(default_config_files=["params.conf"])

if __name__ == "__main__":
    print("Retrieving data and preparing targets.")

    data = retrieve_csv(CONF.csv_path)
    x, y, norm_params = prepare_targets(data, CONF.sequence_length)

    # Three-way split: train / val / test (no shuffle — time series)
    train_end = int(len(x) * CONF.training_slice)
    val_end = int(len(x) * (1 - (1 - CONF.training_slice) / 2))

    x_train, y_train = x[:train_end], y[:train_end]
    x_val, y_val = x[train_end:val_end], y[train_end:val_end]
    x_test, y_test = x[val_end:], y[val_end:]

    train_pct = len(x_train) * 100 // len(x)
    val_pct = len(x_val) * 100 // len(x)
    test_pct = len(x_test) * 100 // len(x)
    print(f"Split: train={train_pct}% ({len(x_train)}), val={val_pct}% ({len(x_val)}), test={test_pct}% ({len(x_test)})")

    # Initialize model and input.
    input = layers.Input(shape=(CONF.sequence_length, 12))
    model = TrafficModel()
    output = model(input)
    model.summary()

    model.compile(optimizer="adam", loss="huber")

    print("Training starting.")
    training_time = time.time()

    early_stop = EarlyStopping(
        monitor="val_loss", patience=10, restore_best_weights=True
    )

    history = model.fit(
        x_train,
        y_train,
        validation_data=(x_val, y_val),
        epochs=CONF.epochs,
        batch_size=CONF.batch_size,
        callbacks=[early_stop],
    )

    # Evaluate on test set
    test_loss = model.evaluate(x_test, y_test, verbose=0)
    print(f"Test loss (unseen data): {test_loss:.6f}")

    # Generate plots
    os.makedirs("plots", exist_ok=True)
    plot_loss(history)

    # Plot predictions on TEST set for an unbiased evaluation
    test_predictions = model.predict(x_test)
    plot_predictions(y_test, test_predictions, norm_params["columns"])

    # Save model
    os.makedirs(os.path.dirname(CONF.model_path), exist_ok=True)
    model.save(CONF.model_path)
    print(f"Model saved: {CONF.model_path}")

    print(f"Training ended successfully in {int(time.time()-training_time)}s")
