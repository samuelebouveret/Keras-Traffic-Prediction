import argparse
import csv
import os

from mininet.node import RemoteController


def build_controller():
    """Returns the remote controller for OpenFlow 1.3: 6653"""
    return dict(name="c0", controller=RemoteController, ip="127.0.0.1", port=6653)


def parse_args():
    """Argument parser for network."""
    parser = argparse.ArgumentParser(
        description="Run Mininet network with traffic generation for ML training"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=120,
        help="Traffic duration in seconds (only in auto mode)",
    )
    parser.add_argument(
        "--training",
        action="store_true",
        help="Debug traffic generator",
    )
    return parser.parse_args()


def create_dirs(log_folder, data_folder, headers):
    """Create directories and log and csv file. Csv file is only initialized and log file is returned (closed in run_network script).

    Args:
        log_folder (str): Log directory path.
        data_folder (str): Data directory path.
        headers (list(str)): List of headers for csv.
    """
    if not os.path.isdir(log_folder):
        os.mkdir(log_folder)
    if not os.path.isdir(data_folder):
        os.mkdir(data_folder)

    out_logs = open(f"{log_folder}logs.logs", "w")
    with open(f"{data_folder}dataset.csv", mode="w", newline="") as file:
        csv.writer(file).writerow(headers)

    return out_logs
