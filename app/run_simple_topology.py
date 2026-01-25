import os
import sys

from mininet.net import Mininet
from mininet.node import Host, OVSKernelSwitch
from mininet.clean import cleanup
from mininet.link import TCLink
from mininet.cli import CLI

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    # Allow "network" imports when running as a script from app/
    sys.path.insert(0, PROJECT_ROOT)

from network.controller import build_controller
from network.topo_simple import SimplePredictTopo


def start_http_server(host: Host, port: int) -> None:
    host.cmd(f"python3 -m http.server {port} >/tmp/http_server.log 2>&1 &")


def generate_http_traffic(net: Mininet, port: int, repeats: int) -> None:
    server = net.get("srv")
    start_http_server(server, port)
    server_ip = server.IP()

    for host in net.hosts:
        if host.name.startswith("h"):
            host.cmd(
                f"for i in $(seq 1 {repeats}); do "
                f"curl -s http://{server_ip}:{port} >/dev/null; "
                "sleep 1; "
                "done &"
            )


try:
    topo = SimplePredictTopo()
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
    net.pingAll()

    generate_http_traffic(net, port=8000, repeats=10)

    CLI(net)
    net.stop()
finally:
    cleanup()
