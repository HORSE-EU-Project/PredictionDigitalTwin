from mininet.net import Mininet
from mininet.node import CPULimitedHost, OVSKernelSwitch
from mininet.node import Controller, RemoteController, OVSController
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI
from fat_tree import MyTopo

import os
import time
from scapy.all import rdpcap, IP, TCP # Import necessary Scapy components
import matplotlib.pyplot as plt
import numpy as np

def start_tcpdump(host, interface, output_file):
    """Starts tcpdump on a given host and interface."""
    print(f"Starting tcpdump on {host.name}-{interface} to {output_file}")
    # -i: interface, -w: write to file, -s0: capture full packets
    # -vvv: verbose output (optional), & to run in background
    host.cmd(f'tcpdump -i {interface} -w {output_file} -s0 &')

def stop_tcpdump(host):
    """Stops tcpdump process on a given host."""
    print(f"Stopping tcpdump on {host.name}")
    host.cmd('killall -q tcpdump') # -q for quiet, avoids "No matching processes found"

def plot_throughput_from_pcap(pcap_file, output_plot_file="throughput_plot.png"):
    """
    Parses a PCAP file to calculate and plot TCP throughput over time.
    Assumes the PCAP contains traffic relevant to a single TCP flow
    or aggregates all TCP traffic.
    """
    if not os.path.exists(pcap_file):
        print(f"Error: PCAP file not found at {pcap_file}")
        return

    print(f"Analyzing PCAP file: {pcap_file}")
    packets = rdpcap(pcap_file)

    timestamps = []
    byte_counts = []

    # Extract TCP payload length and timestamp
    for pkt in packets:
        if pkt.haslayer(IP) and pkt.haslayer(TCP):
            # Calculate actual data length (IP total length - IP header - TCP header)
            # This is a more accurate way to get the payload size for TCP throughput
            payload_len = len(pkt[TCP].payload)
            if payload_len > 0: # Only consider packets with actual data
                timestamps.append(float(pkt.time)) # pkt.time is the timestamp of the packet
                byte_counts.append(payload_len)

    if not timestamps:
        print("No TCP packets with payload found in the PCAP file to plot throughput.")
        return

    # Convert to numpy arrays for easier processing
    timestamps = np.array(timestamps)
    byte_counts = np.array(byte_counts)

    # Calculate time bins (e.g., 1-second intervals)
    start_time = timestamps[0]
    end_time = timestamps[-1]
    duration = end_time - start_time
    if duration <= 0:
        print("Duration is zero or negative. Cannot plot throughput.")
        return

    # Define bin size (e.g., 1 second)
    bin_size = 0.1 # seconds, for finer granularity
    num_bins = int(np.ceil(duration / bin_size))
    if num_bins == 0:
        num_bins = 1 # Ensure at least one bin if duration is very small

    bins = np.arange(start_time, end_time + bin_size, bin_size)

    # Use np.histogram to sum bytes in each bin
    # 'weights' argument sums the byte_counts for packets falling into each bin
    bytes_per_bin, _ = np.histogram(timestamps, bins=bins, weights=byte_counts)

    # Calculate throughput in Mbps
    # (bytes * 8 bits/byte) / (bin_size in seconds) / (1024*1024 bits/Mbps)
    throughput_mbps = (bytes_per_bin * 8) / bin_size / (1024 * 1024)

    # Time points for plotting (mid-points of bins)
    time_points = bins[:-1] + bin_size / 2

    # Plotting
    plt.figure(figsize=(12, 6))
    plt.plot(time_points - start_time, throughput_mbps, marker='o', linestyle='-', markersize=4)
    plt.title(f'TCP Throughput from {pcap_file.split("/")[-1]}')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Throughput (Mbps)')
    plt.grid(True)
    plt.ylim(bottom=0) # Ensure y-axis starts at 0
    plt.tight_layout()
    plt.savefig(output_plot_file)
    print(f"Throughput plot saved to {output_plot_file}")
    plt.show() # Display the plot

def myNetworkWithTrafficAnalysis():
    "Creates a Mininet network, sets TCP BBR, captures traffic, and plots throughput."

    # Define PCAP file paths
    # It's good practice to save PCAPs in a specific directory or a temporary one
    output_dir = "/tmp/mininet_traffic"
    os.makedirs(output_dir, exist_ok=True) # Ensure directory exists

    h1_pcap = os.path.join(output_dir, 'h1_traffic.pcap')
    h2_pcap = os.path.join(output_dir, 'h2_traffic.pcap')

    # Clean up previous pcap files
    if os.path.exists(h1_pcap): os.remove(h1_pcap)
    if os.path.exists(h2_pcap): os.remove(h2_pcap)


    net = Mininet(topo=MyTopo(), host=CPULimitedHost, switch=OVSKernelSwitch, link=TCLink, controller=RemoteController)

    # c1 = net.addController(name='c1', controller=RemoteController)

    #print("*** Adding hosts and switch")
    #h1 = net.addHost('h1', ip='10.0.0.1/24')
    #h2 = net.addHost('h2', ip='10.0.0.2/24')
    #s1 = net.addSwitch('s1')

    #print("*** Creating links")
    #net.addLink(h1, s1)
    #net.addLink(h2, s1)

    print("*** Starting network")
    net.start()

    print("*** Checking network connectivity")
    dumpNodeConnections(net.hosts)
    net.pingAll()

    print("\n*** Verifying available congestion control algorithms on h1:")
    h1.cmd('sysctl net.ipv4.tcp_available_congestion_control')

    print("\n*** Setting TCP congestion control to BBR for h1 and h2")
    h1.cmd('modprobe tcp_bbr')
    h2.cmd('modprobe tcp_bbr')
    h1.cmd('sysctl -w net.ipv4.tcp_congestion_control=bbr')
    h2.cmd('sysctl -w net.ipv4.tcp_congestion_control=bbr')

    print("\n*** Verifying active congestion control on h1 and h2:")
    h1.cmd('sysctl net.ipv4.tcp_congestion_control')
    h2.cmd('sysctl net.ipv4.tcp_congestion_control')

    # --- Traffic Capture Setup ---
    print("\n*** Preparing for traffic capture...")
    # Determine the interface names
    h1_intf = h1.intfNames()[0] # e.g., 'h1-eth0'
    h2_intf = h2.intfNames()[0] # e.g., 'h2-eth0'

    # Start tcpdump on h1's interface (to capture traffic going into/out of h1)
    start_tcpdump(h1, h1_intf, h1_pcap)
    # You could also start tcpdump on the switch interface, but capturing at host
    # is often more relevant for host-specific throughput.

    # Give tcpdump a moment to start
    time.sleep(1)

    print("\n*** Running iperf test to generate traffic with BBR")
    print("Starting iperf server on h1 (port 5001)...")
    h1.cmd('iperf -s -p 5001 &')

    print("Running iperf client from h2 to h1 for 10 seconds...")
    iperf_output = h2.cmd('iperf -c 10.0.0.1 -p 5001 -b 10m -t 10')
    print("Iperf client output:\n", iperf_output)

    # Give tcpdump a moment to finish writing its buffer
    time.sleep(2)

    print("\n*** Stopping tcpdump")
    stop_tcpdump(h1)

    # Stop iperf server on h1
    h1.cmd('kill %iperf')

    # --- Traffic Analysis and Plotting ---
    print("\n*** Analyzing captured traffic and plotting throughput...")
    plot_throughput_from_pcap(h1_pcap, os.path.join(output_dir, 'h1_throughput.png'))


    print("\n*** Entering Mininet CLI. Type 'exit' to quit.")
    CLI(net)

    print("*** Stopping network")
    net.stop()

if __name__ == '__main__':
    # Set the logging level for Mininet
    setLogLevel('info')
    # Check for required libraries
    try:
        import scapy
        import matplotlib
        import numpy
    except ImportError:
        print("Error: Missing required Python libraries.")
        print("Please install them: pip install scapy matplotlib numpy")
        exit(1)

    myNetworkWithTrafficAnalysis()
