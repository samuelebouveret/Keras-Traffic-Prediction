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

if not os.path.isdir("logs"):
    os.mkdir("logs")
if not os.path.isdir("data"):
    os.mkdir("data")

out_logs = open("logs/out.logs", "w")
err_logs = open("logs/err.logs", "w")
in_logs = open("logs/in.logs", "w")


if __name__ == "__main__":
    try:
        # TODO -- Remove unused logs files (in/out?)
        controller_child = subprocess.Popen(
            ["ryu-manager", "network/ryu_controller.py"],
            stdout=out_logs,
            stderr=err_logs,
            stdin=in_logs,
        )
        print(f"Started controller/logger process with PID {controller_child.pid}.")

        print("Creating network.")
        topo = PredictTopo()
        net = Mininet(
            topo=topo,
            link=TCLink,
            controller=None,
            switch=OVSKernelSwitch,
            # autoSetMacs=True,
            # autoStaticArp=True,
        )
        net.addController(**build_controller())

        print("Starting network.")
        net.start()
        setLogLevel("info")

        net.pingAll()

        generate_http_traffic(net, port=8000, repeats=10)

        CLI(net)
        print("Stopping network.")
        net.stop()
    finally:
        print("Terminating ruy-manager process and cleaning mininet data.")
        controller_child.terminate()
        setLogLevel()
        cleanup()
        in_logs.close()
        err_logs.close()
        out_logs.close()
        print("Execution ended succesfully.")
