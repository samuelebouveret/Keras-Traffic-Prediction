from mininet.topo import Topo


class SimplePredictTopo(Topo):
    """Simple 3-switch topology with an HTTP server for traffic generation."""

    def __init__(
        self,
        hosts_per_edge=3,
        h_bw=5,
        s_bw=10,
        delay="5ms",
        max_queue_size=1000,
        loss=0,
        use_htb=True,
    ):
        self.hosts_per_edge = hosts_per_edge
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

    def build(self):
        core = self.addSwitch("s1", protocols="OpenFlow13")
        edge_a = self.addSwitch("s2", protocols="OpenFlow13")
        edge_b = self.addSwitch("s3", protocols="OpenFlow13")

        server = self.addHost("srv")
        self.addLink(server, core, **self.host_opts)

        for i in range(1, self.hosts_per_edge + 1):
            host = self.addHost(f"h{i}")
            self.addLink(host, edge_a, **self.host_opts)

        start = self.hosts_per_edge + 1
        end = start + self.hosts_per_edge
        for i in range(start, end):
            host = self.addHost(f"h{i}")
            self.addLink(host, edge_b, **self.host_opts)

        self.addLink(edge_a, core, **self.switch_opts)
        self.addLink(edge_b, core, **self.switch_opts)
