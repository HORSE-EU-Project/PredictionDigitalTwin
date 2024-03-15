from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ipv4, ethernet

import time
import pandas as pd
from sklearn.linear_model import LinearRegression

class TrafficPredictionController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(TrafficPredictionController, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.flow_data = {}  # Dictionary to store traffic data for each data flow

    @set_ev_cls(ofp_event.EventOFPStateChange, [CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            self.logger.info("Switch %s connected", datapath.id)
            self.datapaths[datapath.id] = datapath

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth and eth.ethertype == 0x0800:
            ipv4_header = pkt.get_protocol(ipv4.ipv4)
            if ipv4_header:
                datapath = msg.datapath
                timestamp = time.time()

                src_ip = ipv4_header.src
                dst_ip = ipv4_header.dst
                flow_key = (src_ip, dst_ip)

                # Initialize traffic data for the flow if it doesn't exist
                if flow_key not in self.flow_data:
                    self.flow_data[flow_key] = {'timestamp': [], 'packet_count': []}

                # Extract packet count from the OpenFlow message
                packet_count = msg.total_len

                # Update traffic data for the flow
                self.flow_data[flow_key]['timestamp'].append(timestamp)
                self.flow_data[flow_key]['packet_count'].append(packet_count)

                # Perform prediction whenever new data arrives for the flow
                prediction = self.perform_traffic_prediction(flow_key)
                if prediction is not None:
                    self.logger.info("Predicted Packet Count for Flow %s: %.2f", flow_key, prediction)

                # Display flows and predicted values
                self.display_flows_and_predictions()


    def perform_traffic_prediction(self, flow_key):
        if len(self.flow_data[flow_key]['timestamp']) < 2:
            # Insufficient data for prediction
            return None

        df = pd.DataFrame(self.flow_data[flow_key])
        X = df['timestamp'].values.reshape(-1, 1)
        y = df['packet_count'].values

        # Simple linear regression model
        model = LinearRegression()
        model.fit(X, y)

        # Predict the next timestamp
        next_timestamp = time.time() + 1
        prediction = model.predict([[next_timestamp]])

        return prediction[0]


    def display_flows_and_predictions(self):
        self.logger.info("Current Flows and Predictions:")
        for flow_key, data in self.flow_data.items():
            last_packet_count = data['packet_count'][-1] if data['packet_count'] else None
            prediction = self.perform_traffic_prediction(flow_key)

            # Check if last_packet_count is None and handle it gracefully
            if last_packet_count is not None:
                self.logger.info("Flow %s - Last Packet Count: %s, Predicted Packet Count: %.2f", flow_key, last_packet_count, prediction)
            else:
                self.logger.info("Flow %s - No recorded packet count, Predicted Packet Count: %.2f", flow_key, prediction)


if __name__ == '__main__':
    from ryu.cmd import manager
    manager.main()
