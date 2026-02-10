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
cfg.CONF(sys.argv[1:])

if __name__ == "__main__":
    print("Retrieving data and preparing targets.")
    data = retrieve_csv(CONF.csv_path)
    predict, target = prepare_targets(data, CONF.sequence_length)

    print(
        f"Splitting data: training->{int(CONF.training_slice*100)}% - validation->{int((100-CONF.training_slice*100))}%."
    )
    split = int(len(predict) * CONF.training_slice)
    x_train, x_val = predict[:split], predict[split:]
    y_train, y_val = target[:split], target[split:]

    input = layers.Input(shape=(CONF.sequence_length, 12))
    model = TrafficModel()
    output = model(input)
    model.summary()

    model.compile(optimizer="adam", loss="mse", metrics=["mae"])

    print("Training starting.")
    training_time = time.time()
    history = model.fit(
        x_train,
        y_train,
        validation_data=(x_val, y_val),
        epochs=CONF.epochs,
        batch_size=CONF.batch_size,
    )

    # Generate plots
    os.makedirs("plots", exist_ok=True)
    plot_loss(history)

    predictions = model.predict(x_val)
    plot_predictions(y_val[:, 0], predictions[:, 0])  # Plot first feature

    # Save model
    os.makedirs(os.path.dirname(CONF.model_path), exist_ok=True)
    model.save(CONF.model_path)
    print(f"Model saved: {CONF.model_path}")

    print(f"Training ended succesfully in {int(time.time()-training_time)}s")
