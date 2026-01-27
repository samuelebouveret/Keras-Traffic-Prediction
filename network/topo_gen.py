from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.clean import cleanup


class PredictTopo(Topo):
    """Overrides __init__ and build functions as in mininet documentation, separating parameteres in __init__ from topology implementation in build for readability.
    """

    def __init__(
        self, h_bw=5, s_bw=10, delay="5ms", max_queue_size=1000, loss=0, use_htb=True
    ):
        """Defines switch-switch and host-switch links options. 

        Args:
            h_bw (int, optional): host-switch link bandwidth. Defaults to 5(Mbps).
            s_bw (int, optional): switch-switch link bandwidth. Defaults to 10(Mbps).
            delay (str, optional): packet delay. Defaults to "5ms".
            max_queue_size (int, optional): maximum packet in queue before dropping. Defaults to 1000.
            loss (int, optional): packet loss percentage. Defaults to 0(%).
            use_htb (bool, optional): allows bw implementation. Defaults to True.
        """

        self.host_opts = dict(
            bw=h_bw,
            delay=delay,
            loss=loss,
            max_queue_size=max_queue_size,
            use_htb=use_htb,
        )
        self.switch_opts = dict(
            bw=s_bw,
            delay=delay,
            loss=loss,
            max_queue_size=max_queue_size,
            use_htb=use_htb,
        )

        Topo.__init__(self)

    # TODO -- Update docstring with final topology explanation.
    def build(self):
        """Functon called at the end of __init__ from Topo class. It creates the actual topology of the network. """

        switch1 = self.addSwitch("s1")
        switch2 = self.addSwitch("s2")
        switch3 = self.addSwitch("s3")

        srv = self.addHost("srv")
        self.addLink(srv, switch3, **self.host_opts)

        for i in range(1, 4):
            host = self.addHost(f"h{i}")
            self.addLink(host, switch1, **self.host_opts)

        for i in range(4, 7):
            host = self.addHost(f"h{i}")
            self.addLink(host, switch2, **self.host_opts)

        # self.addLink(switch1, switch2, **self.switch_opts)

        self.addLink(switch1, switch3, **self.switch_opts)

        self.addLink(switch2, switch3, **self.switch_opts)


def test_topology():
    """Generates and tests the default PredictTopo topology with the pingAll function. """

    print("Running ping test on topology.")
    topo = PredictTopo()
    net = Mininet(topo=topo, link=TCLink)
    net.start()
    print("Starting pingAll.")
    net.pingAll()
    print("PingAll finished.")
    net.stop()
    print("Cleaning -> mn -c.")
    cleanup()
    print("Test end.")


if __name__ == "__main__":
    setLogLevel("info")
    test_topology()
