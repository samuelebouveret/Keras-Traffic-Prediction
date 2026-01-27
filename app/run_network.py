import os
import sys

from mininet.net import Mininet
from mininet.node import Host, OVSKernelSwitch
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


if __name__ == "__main__":
    try:
        topo = PredictTopo()
        net = Mininet(
            topo=topo,
            link=TCLink,
            controller=None,
            switch=OVSKernelSwitch,
            autoSetMacs=True,
            autoStaticArp=True,
        )
        net.addController(**build_controller())

        net.start()
        setLogLevel("info")

        net.pingAll()

        generate_http_traffic(net, port=8000, repeats=10)

        CLI(net)
        net.stop()
    finally:
        setLogLevel()
        cleanup()
