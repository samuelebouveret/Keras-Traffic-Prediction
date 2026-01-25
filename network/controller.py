from mininet.node import RemoteController

def build_controller():
    # Porta tipica per OpenFlow 1.3: 6653 (spesso 6633 per OF1.0)
    return dict(
        name="c0",
        controller=RemoteController,
        ip="127.0.0.1",
        port=6633,
    )