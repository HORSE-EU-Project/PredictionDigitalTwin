#!/usr/bin/python3

#from scapy.all import *
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

  
interval = config['FLOW']['interval']
pf = config['PCAP']['pcap_name']


if not os.path.exists(pf):
    print(f"Errore: il file {pf} non esiste.")
    exit(1)

#already in the SH file
directory = "output_tcpdump"
if not os.path.exists(directory):
    os.system(f"mkdir {directory}")


directory2 = "output_pcap"
if not os.path.exists(directory2):
    os.system(f"mkdir {directory2}")
    
directory3 = "attacks"
if not os.path.exists(directory3):
    os.system(f"mkdir {directory3}")
    
f = open(pf, 'rb')
pcap = dpkt.pcap.Reader(f)

print(f"Open PCAP file: {pf}")

counter = 0
first_time=0
p_len =0

#flows =[]
# Struttura di dati per memorizzare i flussi
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

#def update_flow(flows, ipsrc, ipdst, timestamp, src_port, dst_port, protocol, flags, packet_length):
def update_flow(flows, ipsrc, ipdst, timestamp, src_port, dst_port, protocol, flags, payload_length):
    key = (ipsrc, ipdst)
    flow = flows[key]
    flow['timestamps'].append(datetime.utcfromtimestamp(timestamp))
    flow['src_ports'].append(src_port)
    flow['dst_ports'].append(dst_port)
    flow['protocols'].append(protocol)
    flow['flags'].append(flags)
    flow['packet_lengths'].append(payload_length)
    flow['total_packets'] += 1
    flow['total_bytes'] += packet_length

# store counts and details for attack ddos detection
ip_count_src = defaultdict(int)
ip_count_dst = defaultdict(int)
syn_count = 0
total_packets = 0

# DNS detection
dns_queries = defaultdict(int)
dns_responses = defaultdict(int)


def get_tcp_flags(flags):
    flag_names = []
    if flags & dpkt.tcp.TH_FIN:
        flag_names.append('FIN') #1
    if flags & dpkt.tcp.TH_SYN:
        flag_names.append('SYN') #2
    if flags & dpkt.tcp.TH_RST:
        flag_names.append('RST') #reset 4
    if flags & dpkt.tcp.TH_PUSH:
        flag_names.append('PSH') #push 8
    if flags & dpkt.tcp.TH_ACK:
        flag_names.append('ACK') #16
    if flags & dpkt.tcp.TH_URG:
        flag_names.append('URG') #32
    return flag_names
    
    
t = datetime.now().strftime('%H_%M_%S')
outfile2 = open("output_tcpdump/packets_len_"+str(interval)+"sec_"+str(t)+".csv","w")

all_flow_records = []  # ⬅️ Lista per salvare le righe con timestamp corretti


writer2 = csv.writer(outfile2)
writer2.writerow(["ds", "ipsrc", "ipdst", "throughput"])

config['OUTPUT_TCPDUMP_ANALYZER']['pkt_len_'+str(interval)+'sec'] = 'packets_len_'+str(interval)+'sec_'+str(t)+'.csv'
config['OUTPUT_TCPDUMP_ANALYZER']['traffic'] = 'output_pcap/traffic_components_'+str(t)+'.csv'
with open('config.ini', 'w') as configfile:
  config.write(configfile)

log_file = "output_pcap/flows_detailed_"+str(t)+".log"
flow_file = 'output_pcap/flows_available_'+str(t)+'.txt'
log_file_w = open(log_file, 'a')

# Mappa dei numeri dei protocolli ai loro nomi
protocols = {6: 'TCP', 17: 'UDP', 1: 'ICMP', 112:'VRRP'}

def process_gtp_packet(packet, ts, ip_src, ip_dst):
    # GTP header è 8 bytes 
    gtp_header_len = 8
    if len(packet) < gtp_header_len:
        return
    gtp_version = (packet[0] & 0xE0) >> 5 
    if gtp_version == 1:
        gtp_msg_type = packet[1] # T-PDU per GTP
        gtp_length = int.from_bytes(packet[2:4], byteorder='big')
        gtp_teid = int.from_bytes(packet[4:8], byteorder='big')
        gtp_payload = packet[8:8+gtp_length]
       
        # For GTP, typically src_port=2152 and dst_port=2152
        src_port, dst_port = 2152, 2152
        protocol = 'GTP'
        flags = ''
        #packet_length = len(packet)
        
        payload_length = len(packet) - gtp_header_len

        ipsrc, ipdst = ip_src, ip_dst
        #update_flow(flows, ipsrc, ipdst, ts, src_port, dst_port, protocol, flags, packet_length)
        update_flow(flows, ipsrc, ipdst, timestamp, src_port, dst_port, protocol, flags, payload_length)

import binascii


def extract_gtp_encapsulated_packet(udp):
    gtp = udp.data
    
    # Start scanning the payload after the initial 8 bytes of GTP header
    payload = gtp[8:]
    
    # Manually search for the start of the IP header (0x45 for IPv4)
    ip_start = None
    for i in range(len(payload)):
        if payload[i] == 0x45:  # Look for the IPv4 header indicator
            ip_start = i
            break
    
    if ip_start is None:
        #print("No IP header found in GTP payload.")  # Debugging information
        return None
    
    #print("Found possible IP header at offset "+str(ip_start))  # Debugging information
    
    # Attempt to parse the IP packet starting from the identified IP header
    try:
        ip_encapsulated = dpkt.ip.IP(payload[ip_start:])
        #print("Successfully extracted IP packet from GTP.")  # Debugging information
        return ip_encapsulated
    except dpkt.UnpackError as e:
        #print("Failed to unpack IP from GTP: "+str(e))  # Debugging information
        return None

# For each packet in the pcap process the contents
print("Starting elaborating packets ...")
for timestamp, buf in pcap:
    
    # Print out the timestamp in UTC
    #print('\nTimestamp: '+str(datetime.utcfromtimestamp(timestamp)))

    # Unpack the Ethernet frame (mac src/dst, ethertype)
    eth = dpkt.ethernet.Ethernet(buf)
    #print('\nEthernet Frame: '+str(mac_addr(eth.src))+""+str(mac_addr(eth.dst)))

    # Make sure the Ethernet frame contains an IP packet
    if not isinstance(eth.data, dpkt.ip.IP):
        #print('Non IP Packet type not supported %s\n' % eth.data.__class__.__name__)
        continue

    # Now unpack the data within the Ethernet frame (the IP packet)
    # Pulling out src, dst, length, fragment info, TTL, and Protocol
    ip = eth.data
   
    # Pull out fragment information (flags and offset all packed into off field, so use bitmasks)
    do_not_fragment = bool(ip.off & dpkt.ip.IP_DF)
    more_fragments = bool(ip.off & dpkt.ip.IP_MF)
    fragment_offset = ip.off & dpkt.ip.IP_OFFMASK

    # IP SOURCE
    ipsrc = socket.inet_ntoa(ip.src) #converte IP in stringa leggibile
        
    # IP DEST
    ipdst = socket.inet_ntoa(ip.dst)
    
    # PROTOCOL
    protocol = ip.get_proto(ip.p).__name__
    
    packet_length = ip.len
    
    # Calcolo della lunghezza del payload
    payload_length = ip.len - (ip.hl * 4) - (ip.data.off * 4 if hasattr(ip.data, 'off') else 0)

    
    # Extract transport layer data if TCP or UDP
    if protocol == 'TCP' and isinstance(ip.data, dpkt.tcp.TCP):
        tcp = ip.data   
        src_port = tcp.sport
        dst_port = tcp.dport
        flags = get_tcp_flags(tcp.flags)
        if tcp.flags & dpkt.tcp.TH_SYN: # Check for SYN packets --- TO FIND SYN FLOOD ---
            syn_count += 1 
    elif protocol == 'UDP' and isinstance(ip.data, dpkt.udp.UDP):
        udp = ip.data
        src_port = udp.sport
        dst_port = udp.dport
        flags = None
         # Check if the UDP packet is using the GTP-U port (2152)
        if udp.dport == 2152 or udp.sport == 2152:
            #print(f"Found GTP-U packet: UDP Source Port: {udp.sport}, Destination Port: {udp.dport}")  # Debugging information
            
            # Extract the encapsulated IP packet from the GTP-U payload
            ip_encapsulated = extract_gtp_encapsulated_packet(udp)
            
            if ip_encapsulated:
                # Check if the encapsulated packet is UDP
                if isinstance(ip_encapsulated.data, dpkt.udp.UDP):
                    udp_inner = ip_encapsulated.data
                    #print(udp_inner.dport)
                    # Check if the destination port of the encapsulated packet is 53 (DNS)
                    if udp_inner.dport == 53:
                        src_ip_inner = socket.inet_ntoa(ip_encapsulated.src)
                        dst_ip_inner = socket.inet_ntoa(ip_encapsulated.dst)
                        ip_count_src[src_ip_inner] += 1
                        ip_count_dst[dst_ip_inner] += 1  
                        #print(f'Encapsulated packet: Source IP {src_ip_inner}, Destination IP {dst_ip_inner}, Destination Port: {udp_inner.dport}')
                        update_flow(flows, src_ip_inner, dst_ip_inner, timestamp, udp_inner.sport, udp_inner.dport, "GTP<DNS>", flags, payload_length)
                    #else:
                    #    print("Encapsulated UDP packet is not DNS (not port 53)")  # Debugging information
                #else:
                    #print("Encapsulated packet is not UDP.")  # Debugging information
            #else:
               # print("No IP packet extracted from GTP.")  # Debugging information
        # Check if the UDP packet is using the GTP-U port (2152)
        #if udp.dport == 2152:
         #   process_gtp_packet(udp.data, timestamp, ipsrc, ipdst)
    else:
        src_port = dst_port = None
        flags = None
    
    #print('IP: %s -> %s   \n (len=%d ttl=%d DF=%d MF=%d offset=%d)\n Protocol: %s' % \
     #   (ipsrc, ipdst, ip.len, ip.ttl, do_not_fragment, more_fragments, fragment_offset, protocol))
  
 
    ### ATTACK DETECTION information needed
    total_packets += 1
    # Count IP occurrences
    ip_count_src[ipsrc] += 1
    ip_count_dst[ipdst] += 1  
    
    time_ms = datetime.utcfromtimestamp(timestamp)
    time_s = time_ms.strftime("%Y-%m-%d %H:%M:%S")

    if first_time == 0:
        time_ss = time_ms + timedelta(seconds=int(interval))
        time_sec = time_ss.strftime("%Y-%m-%d %H:%M:%S")
        first_time = 1

    elif time_s == time_sec:
        time_ss = time_ms + timedelta(seconds=int(interval))
        time_sec = time_ss.strftime("%Y-%m-%d %H:%M:%S")

        # Calcola throughput per ogni flusso separato
        for (ipsrc, ipdst), flow in flows.items():
            if flow['packet_lengths']:
                bytes_sum = sum(flow['packet_lengths'])
                bitsec = (bytes_sum * 8) / int(interval)
                current_throughput = round(bitsec)

                # Scrivi nel CSV principale
                writer2.writerow([str(time_s), ipsrc, ipdst, current_throughput])

                # Salva per output dettagliato
                all_flow_records.append([
                    ipsrc,
                    ipdst,
                    str(time_s),  # timestamp dell’intervallo corrente
                    None,
                    None,
                    flow["protocols"][0] if flow["protocols"] else None,
                    "",
                    bytes_sum,
                    current_throughput
                ])

                # Aggiorna dizionario (opzionale, se serve più avanti)
                flow['throughput'] = current_throughput

        # Reset pacchetti per intervallo successivo
        for flow in flows.values():
            flow['packet_lengths'] = []


    
    if dst_port == 2152:
        process_gtp_packet(udp.data, timestamp, ipsrc, ipdst)
    else:
        update_flow(flows, ipsrc, ipdst, timestamp, src_port, dst_port, protocol, flags, packet_length)
    
    if total_packets % 100000 == 0:
        print(f"Done {total_packets} packets until now ...")
        
print(f"Finish packet elaboration with total {total_packets}")

# Salvataggio dei dati dei flussi in un file di CSV
detailed_csv_path = f'output_pcap/flows_detailed_{t}.csv'
with open(detailed_csv_path, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['ipsrc', 'ipdst', 'timestamp', 'src_port', 'dst_port', 'protocol', 'flags', 'packet_length', 'throughput'])
    writer.writerows(all_flow_records)




config.read('config.ini')
if 'CSV_FLOWS' not in config:
    config.add_section('CSV_FLOWS')

config['CSV_FLOWS']['detailed_file'] = detailed_csv_path

with open('config.ini', 'w', encoding='utf-8') as configfile:
    config.write(configfile)
    
# ----------------------- DDoS/DoS detection ------------------
# Print a summary of potential DoS/DDoS indicators
attacks = open("attacks/IP_info_"+str(t)+".txt", "w")
attacks.write("Total packets: "+str(total_packets)+"\n")
attacks.write("Total SYN packets (no ACK counted): "+str(int(syn_count)/2)+"\n")
attacks.write("Source IP counts:\n")
for ip, count in ip_count_src.items():
    attacks.write(str(ip)+": "+str(count)+"\n")
    
# Check for high volume of traffic
if total_packets > 1000:  # threshold
    attacks.write('High volume of traffic detected.\n')

# Check for SYN flood
if syn_count > 500:  
    attacks.write('Potential SYN flood detected.\n')

# Check for multiple source IPs (potential DDoS)
if len(ip_count_src) > 100:
    attacks.write('Multiple source IPs detected (potential DDoS).\n')

# Check for single source IP with high count (potential DoS)
for ip, count in ip_count_src.items():
    if count > 500: 
        attacks.write('High traffic from single source IP detected (potential DoS): '+str(ip)+' with '+str(count)+' packets.\n')
        
attacks.write("Destination IP counts:\n")
for ip, count in ip_count_dst.items():
    attacks.write(str(ip)+": "+str(count)+"\n")
    
# Check for high volume of traffic
if total_packets > 1000:  # threshold
    attacks.write('High volume of traffic detected.\n')

if len(ip_count_dst) > 100:
    attacks.write('Multiple destitation IPs detected.\n')

# Check for single source IP with high count (potential DoS)
for ip, count in ip_count_dst.items():
    if count > 500: 
        attacks.write('High traffic to single destination IP detected: '+str(ip)+' with '+str(count)+' packets.\n')
# ------------------------------- -----------------------------
'''
# DNS detection summary
dns_summary = open("attacks/DNS_info_"+str(t)+".txt", "w")
dns_summary.write("DNS Queries:\n")
for key, count in dns_queries.items():
    dns_summary.write(f"{key}: {count}\n")
dns_summary.write("DNS Responses:\n")
for key, count in dns_responses.items():
    dns_summary.write(f"{key}: {count}\n")

'''


# Carica il file di configurazione
config = configparser.ConfigParser()
config.read('config.ini')

# Sezione per salvare i dati dei flussi in file CSV separati per IP di destinazione
flows_by_ip_dest = defaultdict(list)

# Organizzare i flussi per IP di destinazione
for (ipsrc, ipdst), flow in flows.items():
    flows_by_ip_dest[ipdst].append((ipsrc, ipdst, flow))

# Conta il numero di flussi trovati
total_flows = len(flows_by_ip_dest)
config['FLOW']['flows'] = str(total_flows)
with open('config.ini', 'w') as configfile:
    config.write(configfile)

# Lista per memorizzare i nomi dei file CSV creati
csv_files = []

# Funzione per calcolare i Mbit/s e scrivere nel CSV
def calculate_bps(flow):
    packets = sorted(zip(flow['timestamps'], flow['packet_lengths']), key=lambda x: x[0])
    start_time = packets[0][0]
    end_time = start_time + timedelta(seconds=5)
    bytes_accumulated = 0
    bps_records = []

    for timestamp, length in packets:
        if start_time <= timestamp < end_time:
            bytes_accumulated += length
        else:
            bps = (bytes_accumulated * 8) / int(interval) # Convert bytes to bits al secondo (bitrate che servirà per iperf3)
            bps_records.append([end_time.strftime("%Y-%m-%d %H:%M:%S"), bps])
            start_time = end_time
            end_time += timedelta(seconds=5)
            bytes_accumulated = length

    if bytes_accumulated > 0:
        bps = (bytes_accumulated * 8) / int(interval)
        bps_records.append([end_time.strftime("%Y-%m-%d %H:%M:%S"), bps])

    return bps_records


# Scrivi le modifiche al file di configurazione
with open('config.ini', 'w') as configfile:
    config.write(configfile)
