import os
import sys
import subprocess
import argparse

from mininet.net import Mininet
from mininet.node import OVSKernelSwitch
from mininet.clean import cleanup
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    # Allow "network" imports when running as a script from app/
    sys.path.insert(0, PROJECT_ROOT)

from network.utils import build_controller
from network.topo_gen import PredictTopo
from network.traffic_gen import run_traffic_scenario, run_training_session

LOG_FOLDER = "logs/"
LOG_FILENAME = "logs"
DATA_FOLDER = "data/"

if not os.path.isdir(LOG_FOLDER):
    os.mkdir(LOG_FOLDER)
if not os.path.isdir(DATA_FOLDER):
    os.mkdir(DATA_FOLDER)

out_logs = open(f"{LOG_FOLDER}{LOG_FILENAME}", "w")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run Mininet network with traffic generation for ML training"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["interactive", "auto"],
        default="interactive",
        help="'interactive' opens CLI, 'auto' runs traffic and exits",
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
        help="Use structured training session instead of random scenario",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
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

        print("Creating network.")
        topo = PredictTopo()
        net = Mininet(topo=topo, link=TCLink, controller=None, switch=OVSKernelSwitch)
        net.addController(**build_controller())

        print("Starting network.")
        net.start()
        setLogLevel("info")

        net.pingAll()

        if args.mode == "interactive":
            print("\n" + "=" * 50)
            print("INTERACTIVE MODE - Traffic commands available:")
            print("  py run_traffic_scenario(net, 60)")
            print("  py run_training_session(net, 120)")
            print("=" * 50 + "\n")
            
            # Import into CLI namespace
            from network.traffic_gen import run_traffic_scenario, run_training_session, TrafficGenerator
            CLI(net)
        else:
            print(f"\nAUTO MODE: Running traffic for {args.duration}s")
            
            if args.training:
                run_training_session(net, total_duration=args.duration)
            else:
                run_traffic_scenario(net, duration=args.duration)
            
            import time
            print(f"\nWaiting for traffic to complete...")
            time.sleep(10)  # Buffer for final traffic to finish
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
