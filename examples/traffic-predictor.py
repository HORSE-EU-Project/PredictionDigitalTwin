from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet

import time
import pandas as pd
from sklearn.linear_model import LinearRegression

class TrafficPredictionController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(TrafficPredictionController, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.traffic_data = {'timestamp': [], 'packet_count': []}

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

        if eth:
            datapath = msg.datapath
            timestamp = time.time()
            packet_count = msg.total_len

            self.traffic_data['timestamp'].append(timestamp)
            self.traffic_data['packet_count'].append(packet_count)

            # Perform prediction whenever new data arrives
            prediction = self.perform_traffic_prediction()
            if prediction is not None:
                self.logger.info("Predicted Packet Count: %.2f", prediction)

    def perform_traffic_prediction(self):
        if len(self.traffic_data['timestamp']) < 2:
            # Insufficient data for prediction
            return None

        df = pd.DataFrame(self.traffic_data)
        X = df['timestamp'].values.reshape(-1, 1)
        y = df['packet_count'].values

        # Simple linear regression model
        model = LinearRegression()
        model.fit(X, y)

        # Predict the next timestamp
        next_timestamp = time.time() + 1
        prediction = model.predict([[next_timestamp]])

        return prediction[0]

if __name__ == '__main__':
    from ryu.cmd import manager
    manager.main()

