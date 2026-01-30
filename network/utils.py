from mininet.node import RemoteController
from mininet.node import Host
from mininet.net import Mininet


def build_controller():
    # Porta tipica per OpenFlow 1.3: 6653 (spesso 6633 per OF1.0)
    return dict(name="c0", controller=RemoteController, ip="127.0.0.1", port=6653)


def _start_http_server(host: Host, port: int) -> None:
    host.cmd(f"python3 -m http.server {port} >/tmp/http_server.log 2>&1 &")


def generate_http_traffic(net: Mininet, port: int, repeats: int) -> None:
    server = net.get("srv")
    _start_http_server(server, port)
    server_ip = server.IP()

    for host in net.hosts:
        if host.name.startswith("h"):
            host.cmd(
                f"for i in $(seq 1 {repeats}); do "
                f"curl -s http://{server_ip}:{port} >/dev/null; "
                "sleep 1; "
                "done &"
            )
