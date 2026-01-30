import os
import sys
import subprocess

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

from network.utils import build_controller, generate_http_traffic
from network.topo_gen import PredictTopo

LOG_FOLDER = "logs/"
LOG_FILENAME = "logs"
DATA_FOLDER = "data/"

if not os.path.isdir(LOG_FOLDER):
    os.mkdir(LOG_FOLDER)
if not os.path.isdir(DATA_FOLDER):
    os.mkdir(DATA_FOLDER)

out_logs = open(f"{LOG_FOLDER}{LOG_FILENAME}", "w")

if __name__ == "__main__":
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

        generate_http_traffic(net, port=8000, repeats=10)

        CLI(net)
        print("Stopping network.")
        net.stop()
        print("Execution ended succesfully.")
    finally:
        print(
            "Terminating ruy-manager process, cleaning mininet data and closing log files."
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
        print("Clenup end.")
