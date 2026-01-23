from mininet.net import Mininet
from mininet.node import Host
from network import PredictTopo
from mininet.clean import cleanup
from mininet.link import TCLink
from mininet.cli import CLI

try:
    topo = PredictTopo()
    net = Mininet(topo=topo, link=TCLink)

    net.start()
    net.pingAll()
    
    http: Host = net.get("http")
    http.cmd("python3 -m http.server 80 &")
    
    h1: Host = net.get("h1")
    output = h1.cmd("curl http://10.0.0.7:80")
    print(output)
    
    net.stop()
finally:
    cleanup()
