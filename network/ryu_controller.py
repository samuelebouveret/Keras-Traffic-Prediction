import time
import csv

from ryu import cfg
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import (
    CONFIG_DISPATCHER,
    MAIN_DISPATCHER,
    DEAD_DISPATCHER,
    set_ev_cls,
)
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import ethernet, ether_types, packet
from ryu.lib import hub


class SimpleForwarding(app_manager.RyuApp):
    """Basic L2 learning switch for OpenFlow 1.3 with logging implementation."""

    # Forza OpenFlow 1.3: deve combaciare con il protocollo degli switch OVS.
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        """Ryu application initialization. It retrieves configuration from params.conf and spawns the monitoring thread."""

        super().__init__(*args, **kwargs)
        CONF = cfg.CONF
        CONF.register_opts(
            [cfg.IntOpt("target_dpid"), cfg.StrOpt("csv_path"), cfg.IntOpt("interval")]
        )

        self.mac_to_port = {}
        self.datapaths = {}

        self.interval = CONF.interval
        self.target_dpid = CONF.target_dpid
        self.csv_path = CONF.csv_path
        self.previous_data = {}

        self.monitor_thread = hub.spawn(self._monitor)

    # --------- SWITCH LOGIC ---------

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        # Installa una regola nella flow table dello switch.
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

        if buffer_id is not None:
            mod = parser.OFPFlowMod(
                datapath=datapath,
                buffer_id=buffer_id,
                priority=priority,
                match=match,
                instructions=inst,
            )
        else:
            mod = parser.OFPFlowMod(
                datapath=datapath, priority=priority, match=match, instructions=inst
            )
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        # Regola di table-miss: invia al controller ciò che non matcha.
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)
        ]
        self.add_flow(datapath, 0, match, actions)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        # Gestione PacketIn: apprende MAC -> porta e decide dove inoltrare.
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match["in_port"]

        # Decodifica il frame Ethernet.
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        # Ignora LLDP (usato per discovery/topologia).
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        dst = eth.dst
        src = eth.src

        # Aggiorna l'apprendimento MAC per questo switch.
        self.mac_to_port.setdefault(datapath.id, {})
        self.mac_to_port[datapath.id][src] = in_port

        # Se conosce la porta di destinazione, inoltra; altrimenti flood.
        if dst in self.mac_to_port[datapath.id]:
            out_port = self.mac_to_port[datapath.id][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # Se non è flood, installa la regola per i pacchetti successivi.
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            self.add_flow(datapath, 1, match, actions)

        # Inoltra il pacchetto corrente.
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data,
        )
        datapath.send_msg(out)

    # --------- LOGGING LOGIC ---------

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        """Logs switch dpids on connection and removes on disconnection."""

        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            self.datapaths.pop(datapath.id, None)

    def _monitor(self):
        """Thread starts in __init__, used to trigger event for logging at determined intervals."""

        # Enforces correct starting time to maintain clean intervals.
        interval = int(self.interval)
        now = time.time()
        next_tick = int(now) + (interval - (int(now) % interval))

        while True:
            sleep_time = next_tick - time.time()
            if sleep_time > 0:
                hub.sleep(sleep_time)

            # Triggers event handler for data logging.
            if self.target_dpid in self.datapaths:
                for dp in self.datapaths.values():
                    ofproto = dp.ofproto
                    parser = dp.ofproto_parser
                    req = parser.OFPPortStatsRequest(dp, 0, ofproto.OFPP_ANY)
                    dp.send_msg(req)
            next_tick += interval

    # TODO -- Maybe add HTTP only packet filtering for specific data traffic prediction.
    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_stats_reply_handler(self, ev):
        """Event handler for data logging and csv writing. It only logs data on the target_dpid from params.conf 
        inside logs/logs.logs file and inside the csv_path file.

        Data is formatted into the csv as follows:
            data = [timestamp, port_n, rx_bytes, tx_bytes, rx_packets,tx_packets]
        where rx/tx data is a delta between the previous switch available data and the current (switch only has 
        cumulative data on this tye of event).
        """

        # Bypass switches with different target_dpid.
        if ev.msg.datapath.id != self.target_dpid:
            return

        for stat in ev.msg.body:
            # Bypass ryu controller port.
            if stat.port_no == 4294967294:
                continue

            key = stat.port_no
            prev = self.previous_data.get(key)

            # Log and write data to csv.
            if prev:
                self.logger.info(f"Port stats for switch {ev.msg.datapath.id}")
                csv_row = []
                timestamp = int(time.time())
                delta_rx = stat.rx_bytes - prev.rx_bytes
                delta_tx = stat.tx_bytes - prev.tx_bytes
                delta_rx_packets = stat.rx_packets - prev.rx_packets
                delta_tx_packets = stat.tx_packets - prev.tx_packets
                csv_row = [
                    timestamp,
                    stat.port_no,
                    delta_rx,
                    delta_tx,
                    delta_rx_packets,
                    delta_tx_packets,
                ]
                self.logger.info(
                    f"Port {stat.port_no}: RX Bytes={delta_rx} - TX Bytes={delta_tx} - RX Packets={delta_rx_packets} - TX Packets={delta_tx_packets} - Timestamp={timestamp}"
                )
                self._write_csv(csv_row)
            self.previous_data[key] = stat

    # TODO -- Might want to change: with open keeps opening and closing 3 times per monitoring.
    def _write_csv(self, row):
        """Writes a row of data into the cvs file with path from params.conf.

        Args:
            row (list): list of data to write.
        """

        with open(self.csv_path, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(row)
