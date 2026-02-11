import os
import sys
import subprocess
import time

from mininet.net import Mininet
from mininet.node import OVSKernelSwitch
from mininet.clean import cleanup
from mininet.link import TCLink
from mininet.log import setLogLevel

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from network.utils import build_controller, parse_args, create_dirs
from network.topo_gen import PredictTopo
from network.traffic_gen import run_traffic_scenario, run_training_session

LOG_FOLDER = "logs/"
DATA_FOLDER = "data/"
HEADERS = ["timestamp", "port", "rx_bytes", "tx_bytes", "rx_packets", "tx_packets"]

if __name__ == "__main__":
    # Directory setup
    out_logs = create_dirs(LOG_FOLDER, DATA_FOLDER, HEADERS)
    args = parse_args()

    # Start ryu controller as subprocess in parallel
    try:
        controller_p = subprocess.Popen(
            [
                "ryu-manager",
                "network/ryu_controller.py",
                "--config-file",
                "params.conf",
            ],
            stderr=out_logs,
        )
        print(f"Started ryu-manager process with PID {controller_p.pid}.")

        # Start network and run traffic
        print("Creating network.")
        topo = PredictTopo()
        net = Mininet(topo=topo, link=TCLink, controller=None, switch=OVSKernelSwitch)
        net.addController(**build_controller())

        print("Starting network.")
        net.start()
        setLogLevel("info")

        # Ping test
        net.pingAll()

        print(f"\nRunning traffic for {args.duration}s")
        if args.training:
            run_training_session(net, total_duration=args.duration)
        else:
            run_traffic_scenario(net, duration=args.duration)

        print(f"\nWaiting for traffic to complete...")
        time.sleep(10)
        print("Traffic generation completed.")

        print("Stopping network.")
        net.stop()
        print("Execution ended successfully.")
    finally:
        print(
            "Terminating ryu-manager process, cleaning mininet data and closing log files."
        )
        controller_p.terminate()

        try:
            controller_p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            controller_p.kill()
            controller_p.wait()

        out_logs.close()
        setLogLevel()
        cleanup()
        print("Cleanup end.")
