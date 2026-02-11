import random
import time
from mininet.net import Mininet


class TrafficGenerator:
    """Generates varied network traffic using iperf and HTTP."""

    def __init__(self, net: Mininet):
        self.net = net
        self.server = net.get("srv")
        self.hosts = [h for h in net.hosts if h.name.startswith("h")]
        self.server_ip = self.server.IP()

    def _start_iperf_server(self, port: int = 5001):
        """Start iperf UDP server."""
        self.server.cmd(f"iperf -s -u -p {port} > /dev/null 2>&1 &")

    def _start_http_server(self, port: int = 8000):
        """Start simple HTTP server."""
        self.server.cmd(f"python3 -m http.server {port} > /dev/null 2>&1 &")

    def _iperf_client(self, host, duration: int, bandwidth: str, port: int = 5001):
        """Run iperf UDP client."""
        host.cmd(
            f"iperf -c {self.server_ip} -u -b {bandwidth} -t {duration} -p {port} > /dev/null 2>&1 &"
        )

    def _http_burst(self, host, requests: int = 5):
        """Send HTTP requests in quick succession."""
        host.cmd(
            f"for i in $(seq 1 {requests}); do "
            f"curl -s http://{self.server_ip}:8000 -o /dev/null; "
            f"done &"
        )

    def start_servers(self):
        """Initialize iperf and HTTP servers."""
        self._start_iperf_server(5001)
        self._start_http_server(8000)
        time.sleep(1)
        print(f"[TrafficGen] Servers started on {self.server_ip}")


def run_traffic_scenario(net: Mininet, duration: int = 60):
    """
    Run a simple traffic scenario with varying intensity.
    
    Pattern:
    - Constant background traffic 
    - Random bursts from different hosts
    - Occasional HTTP requests for variety
    """
    gen = TrafficGenerator(net)
    gen.start_servers()

    print(f"Starting traffic generation for {duration}s")
    start_time = time.time()

    # Background traffic: low constant bandwidth from all hosts
    for host in gen.hosts:
        gen._iperf_client(host, duration=duration, bandwidth="200K")

    # Main loop: add bursts and HTTP traffic
    while time.time() - start_time < duration:
        # Random burst from one host (higher bandwidth)
        burst_host = random.choice(gen.hosts)
        burst_bw = random.choice(["1M", "2M", "3M"])
        burst_duration = random.randint(3, 8)
        
        print(f"Burst: {burst_host.name} -> {burst_bw} for {burst_duration}s")
        gen._iperf_client(burst_host, duration=burst_duration, bandwidth=burst_bw, port=5002)

        # HTTP requests from random hosts
        http_hosts = random.sample(gen.hosts, random.randint(1, 3))
        for h in http_hosts:
            gen._http_burst(h, requests=random.randint(3, 10))

        # Wait before next burst cycle
        wait_time = random.uniform(5, 12)
        time.sleep(min(wait_time, duration - (time.time() - start_time)))

    print("Traffic generation complete")


def run_training_session(net: Mininet, total_duration: int = 120):
    """
    Run a structured training session with distinct phases.
    
    Phases:
    1. Low traffic 
    2. Medium traffic 
    3. High traffic 
    4. Variable traffic 
    """
    gen = TrafficGenerator(net)
    gen.start_servers()

    phase_duration = total_duration // 4
    print(f"Training session: {total_duration}s ({phase_duration}s per phase)")

    # Phase 1: Low traffic
    print("Low traffic")
    for host in gen.hosts:
        gen._iperf_client(host, duration=phase_duration, bandwidth="100K")
    time.sleep(phase_duration)

    # Phase 2: Medium traffic  
    print("Medium traffic")
    for host in gen.hosts:
        gen._iperf_client(host, duration=phase_duration, bandwidth="500K")
        gen._http_burst(host, requests=5)
    time.sleep(phase_duration)

    # Phase 3: High traffic
    print("High traffic")
    for host in gen.hosts:
        gen._iperf_client(host, duration=phase_duration, bandwidth="2M")
    time.sleep(phase_duration)

    # Phase 4: Variable 
    print("Variable traffic")
    phase_start = time.time()
    while time.time() - phase_start < phase_duration:
        host = random.choice(gen.hosts)
        bw = random.choice(["300K", "1M", "2M", "4M"])
        gen._iperf_client(host, duration=3, bandwidth=bw)
        gen._http_burst(host, requests=random.randint(2, 8))
        time.sleep(random.uniform(2, 5))

    print("Training session complete")
