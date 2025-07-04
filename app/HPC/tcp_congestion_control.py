from mininet.net import Mininet
from mininet.node import CPULimitedHost, OVSKernelSwitch
from mininet.node import Controller, RemoteController, OVSController
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI # Import CLI

def myWorkingNetwork():
    "Creates a simple Mininet network, sets TCP BBR, and runs a basic iperf test."

    # Set up Mininet with a default host type (CPULimitedHost for consistency)
    # and a link type (TCLink for potential bandwidth/delay settings, though not used here)
    net = Mininet(host=CPULimitedHost, switch=OVSKernelSwitch, controller=RemoteController, link=TCLink)

    c1 = net.addController(name='c1', controller=RemoteController)

    print("*** Adding hosts and switch")
    h1 = net.addHost('h1', ip='10.0.0.1/24')
    h2 = net.addHost('h2', ip='10.0.0.2/24')
    s1 = net.addSwitch('s1')

    print("*** Creating links")
    # Add links between hosts and switch
    # You can specify parameters like bw, delay, loss if needed
    net.addLink(h1, s1)
    net.addLink(h2, s1)

    print("*** Starting network")
    net.start()

    print("*** Checking network connectivity")
    dumpNodeConnections(net.hosts)
    net.pingAll()

    print("\n*** Verifying available congestion control algorithms on h1:")
    h1.cmd('sysctl net.ipv4.tcp_available_congestion_control')

    print("\n*** Setting TCP congestion control to BBR for h1 and h2")
    # Ensure BBR module is loaded (if not already) and set as default
    h1.cmd('modprobe tcp_bbr')
    h2.cmd('modprobe tcp_bbr')
    h1.cmd('sysctl -w net.ipv4.tcp_congestion_control=bbr')
    h2.cmd('sysctl -w net.ipv4.tcp_congestion_control=bbr')

    print("\n*** Verifying active congestion control on h1 and h2:")
    h1.cmd('sysctl net.ipv4.tcp_congestion_control')
    h2.cmd('sysctl net.ipv4.tcp_congestion_control')

    print("\n*** Running iperf test to demonstrate traffic with BBR")
    # Start iperf server on h1
    print("Starting iperf server on h1 (port 5001)...")
    h1.cmd('iperf -s -p 5001 &') # Run in background

    # Run iperf client from h2 to h1 for 10 seconds
    print("Running iperf client from h2 to h1 for 10 seconds...")
    iperf_output = h2.cmd('iperf -c 10.0.0.1 -p 5001 -t 10')
    print("Iperf client output:\n", iperf_output)

    # Stop iperf server on h1
    h1.cmd('kill %iperf')

    print("\n*** Entering Mininet CLI. Type 'exit' to quit.")
    CLI(net)

    print("*** Stopping network")
    net.stop()

if __name__ == '__main__':
    # Set the logging level for Mininet
    setLogLevel('info')
    myWorkingNetwork()
