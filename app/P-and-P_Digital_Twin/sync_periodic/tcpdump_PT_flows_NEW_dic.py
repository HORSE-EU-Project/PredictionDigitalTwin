#!/usr/bin/python3
#file output: packets_len_*, flows_available_*.txt e flows_detailed_*.csv + flows_detailed_*.txt

import dpkt
import socket
from datetime import datetime, timedelta
import csv
import os
from collections import defaultdict

import configparser
config = configparser.ConfigParser()
try:
    config.read('config.ini')
except Exception as error:
    print("\n Couldn't open config.ini: ", error)

config.sections()

# PARAMETRI DAL CONFIG
try:
    interval = int(config['FLOW']['interval'])
except Exception:
    interval = 5
try:
    pf = config['PCAP']['pcap_name']
except Exception:
    pf = None

if pf is None or not os.path.exists(pf):
    print(f"Errore: il file {pf} non esiste o percorso non impostato.")
    exit(1)

# CREAZIONE CARTELLE OUTPUT SE NON PRESENTI

directory2 = "output_pcap"
if not os.path.exists(directory2):
    os.system(f"mkdir {directory2}")

directory3 = "attacks"
if not os.path.exists(directory3):
    os.system(f"mkdir {directory3}")

def open_pcap(path):
    try:
        f = open(path, 'rb')
    except Exception as e:
        raise RuntimeError(f"Impossibile aprire file pcap: {e}")

    try:
        rdr = dpkt.pcap.Reader(f)
        class DPKTWrapper:
            def __init__(self, rd, fh):
                self._rd = rd
                self._fh = fh
                self.linktype = getattr(rd, 'linktype', None)
            def __iter__(self):
                for ts, buf in self._rd:
                    yield ts, buf
            def close(self):
                try:
                    self._fh.close()
                except:
                    pass
        return DPKTWrapper(rdr, f)
    except Exception:
        pass
   
    raise RuntimeError("Nessun lettore pcap disponibile: installa 'dpkt'.")

def parse_packet_to_ip(buf):

    # Ethernet
    try:
        eth = dpkt.ethernet.Ethernet(buf)
        if isinstance(eth.data, dpkt.ip.IP):
            return eth.data, 'ethernet'
    except Exception:
        pass

    # SLL (Linux Cooked)
    try:
        sll = dpkt.sll.SLL(buf)
        if isinstance(sll.data, dpkt.ip.IP):
            return sll.data, 'sll'
    except Exception:
        pass

    # Raw IP (buffer already IP)
    try:
        ip_tmp = dpkt.ip.IP(buf)
        if hasattr(ip_tmp, 'src') and hasattr(ip_tmp, 'dst'):
            return ip_tmp, 'raw'
    except Exception:
        pass

    return None, None

flows = defaultdict(lambda: {
    'timestamps': [],
    'src_ports': [],
    'dst_ports': [],
    'protocols': [],
    'flags': [],
    'packet_lengths': [],
    'total_packets': 0,
    'total_bytes': 0,
})

def update_flow(flows, ipsrc, ipdst, timestamp, src_port, dst_port, protocol, flags, payload_length):
    key = (ipsrc, ipdst)
    flow = flows[key]
    is_new = len(flow['timestamps']) == 0

    if isinstance(timestamp, (int, float)):
        flow_ts = datetime.utcfromtimestamp(timestamp)
    else:
        flow_ts = timestamp
    flow['timestamps'].append(flow_ts)
    flow['src_ports'].append(src_port)
    flow['dst_ports'].append(dst_port)
    flow['protocols'].append(protocol)
    flow['flags'].append(flags)
    flow['packet_lengths'].append(payload_length)
    flow['total_packets'] += 1
    try:
        flow['total_bytes'] += int(payload_length)
    except Exception:
        pass

    try:
        if is_new:
            flow_list_w.write(f"Flow from {ipsrc} to {ipdst} proto={protocol} srcport={src_port} dstport={dst_port}\n")
            flow_list_w.flush()
    except Exception:
        pass


ip_count_src = defaultdict(int)
ip_count_dst = defaultdict(int)
syn_count = 0
total_packets = 0


dns_queries = defaultdict(int)
dns_responses = defaultdict(int)

def get_tcp_flags(flags):
    flag_names = []
    try:
        if flags & dpkt.tcp.TH_FIN:
            flag_names.append('FIN')
        if flags & dpkt.tcp.TH_SYN:
            flag_names.append('SYN')
        if flags & dpkt.tcp.TH_RST:
            flag_names.append('RST')
        if flags & dpkt.tcp.TH_PUSH:
            flag_names.append('PSH')
        if flags & dpkt.tcp.TH_ACK:
            flag_names.append('ACK')
        if flags & dpkt.tcp.TH_URG:
            flag_names.append('URG')
    except Exception:
        pass
    return flag_names

def extract_gtp_encapsulated_packet(udp):
    gtp = udp.data if hasattr(udp, 'data') else udp
    payload = gtp[8:] if len(gtp) > 8 else b''
    ip_start = None
    for i in range(len(payload)):
        if payload[i] == 0x45:
            ip_start = i
            break
    if ip_start is None:
        return None
    try:
        ip_encapsulated = dpkt.ip.IP(payload[ip_start:])
        return ip_encapsulated
    except Exception:
        return None

def process_gtp_packet(packet, ts, ip_src, ip_dst):
    gtp_header_len = 8
    if len(packet) < gtp_header_len:
        return
    try:
        gtp_version = (packet[0] & 0xE0) >> 5
    except Exception:
        return
    if gtp_version != 1:
        return
    try:
        gtp_length = int.from_bytes(packet[2:4], byteorder='big')
        payload = packet[8:8+gtp_length] if gtp_length > 0 else packet[8:]
    except Exception:
        payload = packet[8:]
    ip_encapsulated = None
    try:
        ip_encapsulated = dpkt.ip.IP(payload)
    except Exception:
        ip_encapsulated = extract_gtp_encapsulated_packet(packet)
    if ip_encapsulated:
        if isinstance(ip_encapsulated.data, dpkt.udp.UDP):
            udp_inner = ip_encapsulated.data
            if getattr(udp_inner, 'dport', None) == 53:
                src_ip_inner = socket.inet_ntoa(ip_encapsulated.src)
                dst_ip_inner = socket.inet_ntoa(ip_encapsulated.dst)
                ip_count_src[src_ip_inner] += 1
                ip_count_dst[dst_ip_inner] += 1
                update_flow(flows, src_ip_inner, dst_ip_inner, ts, getattr(udp_inner, 'sport', None), getattr(udp_inner, 'dport', None), "GTP<DNS>", None, len(getattr(udp_inner, 'data', b"")))


t = datetime.now().strftime('%H_%M_%S')

flow_list_path = f'output_pcap/flows_available_{t}.txt'
flow_list_w = open(flow_list_path, 'w')

config.setdefault('OUTPUT_TCPDUMP_ANALYZER', {})
config['OUTPUT_TCPDUMP_ANALYZER']['flow_list'] = os.path.basename(flow_list_path)
with open('config.ini', 'w') as configfile:
    config.write(configfile)

all_flow_records = []

protocols = {6: 'TCP', 17: 'UDP', 1: 'ICMP', 112:'VRRP'}

reader = open_pcap(pf)
print(f"Apri PCAP file: {pf}")

print("Elaborazione pacchetti ...")

first_time = 0
time_ss = None

for timestamp, buf in reader:
    try:
        if timestamp is None:
            continue
        try:
            ts = float(timestamp)
        except Exception:
            continue

        total_packets += 1


        ip_pkt, link_detected = parse_packet_to_ip(buf)
        if ip_pkt is None:
            continue


        try:
            ipsrc = socket.inet_ntoa(ip_pkt.src)
            ipdst = socket.inet_ntoa(ip_pkt.dst)
        except Exception:
            continue

        proto_num = getattr(ip_pkt, 'p', None)
        protocol = protocols.get(proto_num, str(proto_num))

        try:
            packet_length = int(getattr(ip_pkt, 'len', None) or len(buf))
        except Exception:
            packet_length = len(buf)
        try:
            payload_length = len(getattr(ip_pkt, 'data', b""))
        except Exception:
            payload_length = packet_length

        src_port = None
        dst_port = None
        flags = None

        if isinstance(ip_pkt.data, dpkt.tcp.TCP):
            tcp = ip_pkt.data
            src_port = tcp.sport
            dst_port = tcp.dport
            flags = get_tcp_flags(getattr(tcp, 'flags', 0))
            if getattr(tcp, 'flags', 0) & dpkt.tcp.TH_SYN:
                syn_count += 1
        elif isinstance(ip_pkt.data, dpkt.udp.UDP):
            udp = ip_pkt.data
            src_port = getattr(udp, 'sport', None)
            dst_port = getattr(udp, 'dport', None)
            # GTP-U detection
            if dst_port == 2152 or src_port == 2152:
                try:
                    process_gtp_packet(udp.data, ts, ipsrc, ipdst)
                except Exception:
                    pass
        else:
            # other protocols
            pass

        # attack counters
        ip_count_src[ipsrc] += 1
        ip_count_dst[ipdst] += 1


        time_ms = datetime.utcfromtimestamp(ts)
        if first_time == 0:

            time_ss = time_ms + timedelta(seconds=interval)
            first_time = 1

        while time_ms >= time_ss:
            time_label = time_ss.strftime("%Y-%m-%d %H:%M:%S")

            for (f_ipsrc, f_ipdst), flow in flows.items():
                if flow['packet_lengths']:
                    bytes_sum = sum(flow['packet_lengths'])
                    bitsec = (bytes_sum * 8) / int(interval)
                    current_throughput = round(bitsec)

                    all_row = [
                        f_ipsrc,
                        f_ipdst,
                        time_label,
                        flow['src_ports'][0] if flow['src_ports'] else None,
                        flow['dst_ports'][0] if flow['dst_ports'] else None,
                        flow['protocols'][0] if flow['protocols'] else None,
                        "",
                        bytes_sum,
                        current_throughput
                    ]
                    all_flow_records.append(all_row)

                    flow['throughput'] = current_throughput

            for flow in flows.values():
                flow['packet_lengths'] = []

            time_ss += timedelta(seconds=interval)

        if not (isinstance(ip_pkt.data, dpkt.udp.UDP) and (getattr(ip_pkt.data, 'dport', None) == 2152 or getattr(ip_pkt.data, 'sport', None) == 2152)):
            update_flow(flows, ipsrc, ipdst, ts, src_port, dst_port, protocol, flags, payload_length)

        if total_packets % 100000 == 0:
            print(f"Analizzati {total_packets} pacchetti... continua")

    except Exception as e:
        print(f"errore ts={timestamp}: {e}")
        continue

try:
    reader.close()
except Exception:
    pass

print(f"Totale pacchetti --> {total_packets}")

detailed_csv_path = f'output_pcap/flows_detailed_{t}.csv'
with open(detailed_csv_path, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['ipsrc', 'ipdst', 'timestamp', 'src_port', 'dst_port', 'protocol', 'flags', 'packet_length', 'throughput'])
    writer.writerows(all_flow_records)

try:
    config.read('config.ini')
    if 'CSV_FLOWS' not in config:
        config.add_section('CSV_FLOWS')
    config['CSV_FLOWS']['detailed_file'] = detailed_csv_path
    # update FLOW count properly
    if 'FLOW' not in config:
        config.add_section('FLOW')
    flows_by_ip_dest = defaultdict(list)
    for (ipsrc, ipdst), flow in flows.items():
        flows_by_ip_dest[ipdst].append((ipsrc, ipdst, flow))
    total_flows = len(flows_by_ip_dest)
    config['FLOW']['flows'] = str(total_flows)
    with open('config.ini', 'w', encoding='utf-8') as configfile:
        config.write(configfile)
except Exception as e:
    print(f"Errore aggiornando config.ini: {e}")

# ---------- DDoS/DoS detection summary ----------
attacks = open("attacks/IP_info_"+str(t)+".txt", "w")
attacks.write("Total packets: "+str(total_packets)+"\n")
attacks.write("Total SYN packets (no ACK counted): "+str(int(syn_count)/2)+"\n")
attacks.write("Source IP counts:\n")
for ip, count in ip_count_src.items():
    attacks.write(str(ip)+": "+str(count)+"\n")

if total_packets > 1000:
    attacks.write('High volume of traffic detected.\n')

if syn_count > 500:
    attacks.write('Potential SYN flood detected.\n')

if len(ip_count_src) > 100:
    attacks.write('Multiple source IPs detected (potential DDoS).\n')

attacks.write("Destination IP counts:\n")
for ip, count in ip_count_dst.items():
    attacks.write(str(ip)+": "+str(count)+"\n")

if len(ip_count_dst) > 100:
    attacks.write('Multiple destitation IPs detected.\n')

for ip, count in ip_count_dst.items():
    if count > 500:
        attacks.write('High traffic to single destination IP detected: '+str(ip)+' with '+str(count)+' packets.\n')
attacks.close()


try:
    outfile2.close()
except:
    pass
try:
    flow_list_w.close()
except:
    pass
