#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# First version of the HORSE Digital Twin
# DDOS scenario

# 1. Launch ryu-manager ryu.app.simple_switch_stp_13
# 2. Launch the Digital Twin with "sudo python3 DT_vx.y.py

# Installing traceroute & hping in the UE:
# apt update
# apt install -y hping3
# apt install traceroute

# Examples:
# hping3 -S -p 443 -c 3 google.com
# iperf:
# - UE: iperf3 -B 10.45.0.11 -c 192.168.0.200
# - server: iperf3 -s -B 192.168.0.200

from comnetsemu.cli import CLI
from comnetsemu.net import Containernet, VNFManager
from mininet.link import TCLink
from mininet.log import info, setLogLevel
from mininet.node import OVSKernelSwitch, Controller, RemoteController

from python_modules.Open5GS   import Open5GS

from mininetFastAPI.mininetFastAPI import MininetRest

import json, time, os
from multiprocessing import Process, active_children

if __name__ == "__main__":

    AUTOTEST_MODE = os.environ.get("COMNETSEMU_AUTOTEST_MODE", 0)

    setLogLevel("info")

    prj_folder="/home/vagrant/comnetsemu/app/comnetsemu_5Gnet"
    mongodb_folder="/home/vagrant/mongodbdata"

    # Uncomment to link to sFlow (but first run start.sh script to activate sFlow deamon
    # exec(open('./sflow-rt/extras/sflow.py').read())
    env = dict()

    # net = Containernet(controller=Controller, link=TCLink)
    net = Containernet(
        switch=OVSKernelSwitch,
        build=False,
        link=TCLink)

    info("*** Adding Host for open5gs CP\n")
    cp = net.addDockerHost(
        "cp",
        dimage="my5gc_v2-4-4",
        ip="192.168.0.111/24",
        # dcmd="",
        dcmd="bash /open5gs/install/etc/open5gs/5gc_cp_init.sh",
        docker_args={
            "ports" : { "3000/tcp": 3000 },
            "volumes": {
                prj_folder + "/log": {
                    "bind": "/open5gs/install/var/log/open5gs",
                    "mode": "rw",
                },
                mongodb_folder: {
                    "bind": "/var/lib/mongodb",
                    "mode": "rw",
                },
                prj_folder + "/open5gs/config": {
                    "bind": "/open5gs/install/etc/open5gs",
                    "mode": "rw",
                },
                "/etc/timezone": {
                    "bind": "/etc/timezone",
                    "mode": "ro",
                },
                "/etc/localtime": {
                    "bind": "/etc/localtime",
                    "mode": "ro",
                },
            },
        },
    )


    info("*** Adding Host for open5gs UPF\n")
    env["COMPONENT_NAME"]="upf"
    upf = net.addDockerHost(
        "upf",
        dimage="my5gc_v2-4-4",
        ip="192.168.0.112/24",
        # dcmd="",
        dcmd="bash /open5gs/install/etc/open5gs/temp/5gc_up_init.sh",
        docker_args={
            "environment": env,
            "volumes": {
                prj_folder + "/log": {
                    "bind": "/open5gs/install/var/log/open5gs",
                    "mode": "rw",
                },
                prj_folder + "/open5gs/config": {
                    "bind": "/open5gs/install/etc/open5gs/temp",
                    "mode": "rw",
                },
                "/etc/timezone": {
                    "bind": "/etc/timezone",
                    "mode": "ro",
                },
                "/etc/localtime": {
                    "bind": "/etc/localtime",
                    "mode": "ro",
                },
            },
            "cap_add": ["NET_ADMIN"],
            "sysctls": {"net.ipv4.ip_forward": 1},
            "devices": "/dev/net/tun:/dev/net/tun:rwm"
        }, 
    )

    info("*** Adding gNB\n")
    env["COMPONENT_NAME"]="gnb"
    gnb = net.addDockerHost(
        "gnb", 
        dimage="myueransim_v3-2-6",
        ip="192.168.0.131/24",
        # dcmd="",
        dcmd="bash /mnt/ueransim/open5gs_gnb_init.sh",
        docker_args={
            "environment": env,
            "volumes": {
                prj_folder + "/ueransim/config": {
                    "bind": "/mnt/ueransim",
                    "mode": "rw",
                },
                prj_folder + "/log": {
                    "bind": "/mnt/log",
                    "mode": "rw",
                },
                "/etc/timezone": {
                    "bind": "/etc/timezone",
                    "mode": "ro",
                },
                "/etc/localtime": {
                    "bind": "/etc/localtime",
                    "mode": "ro",
                },
                "/dev": {"bind": "/dev", "mode": "rw"},
            },
            "cap_add": ["NET_ADMIN"],
            "devices": "/dev/net/tun:/dev/net/tun:rwm"
        },
    )

    info("*** Adding UE\n")
    env["COMPONENT_NAME"]="ue"
    ue = net.addDockerHost(
        "ue", 
        dimage="myueransim_v3-2-6",
        ip="192.168.0.132/24",
        # dcmd="",
        dcmd="bash /mnt/ueransim/open5gs_ue_init.sh",
        docker_args={
            "environment": env,
            "volumes": {
                prj_folder + "/ueransim/config": {
                    "bind": "/mnt/ueransim",
                    "mode": "rw",
                },
                prj_folder + "/log": {
                    "bind": "/mnt/log",
                    "mode": "rw",
                },
                "/etc/timezone": {
                    "bind": "/etc/timezone",
                    "mode": "ro",
                },
                "/etc/localtime": {
                    "bind": "/etc/localtime",
                    "mode": "ro",
                },
                "/dev": {"bind": "/dev", "mode": "rw"},
            },
            "cap_add": ["NET_ADMIN"],
            "devices": "/dev/net/tun:/dev/net/tun:rwm"
        },
    )

    info("*** Add remote controller\n")
    c0 = RemoteController( 'c0', ip='127.0.0.1', port=6653 )
    net.addController( c0 )
    

	info("*** Adding switches and hosts")
		cgserver=self.addDockerHost('cgserver', dimage="dev_test", ip="192.168.0.100", docker_args={"hostname": "cgserver"})
		csr1=self.addSwitch('csr1')
		csr4=self.addSwitch('csr4')
		csr5=self.addSwitch('csr5')
		csr6=self.addSwitch('csr6')
		csr7=self.addSwitch('csr7')
		csr2=self.addSwitch('csr2')
		csr3=self.addSwitch('csr3')
		csr11=self.addSwitch('csr11')
		csr12=self.addSwitch('csr12')
		csr13=self.addSwitch('csr13')
		# dnsc10 will be a mobile host configured within EURANSIM
		# dnsc8 will be a mobile host configured within EURANSIM
		# dnsc2 will be a mobile host configured within EURANSIM
		# dnsc1 will be a mobile host configured within EURANSIM
		# dnsc9 will be a mobile host configured within EURANSIM
		# dnsc3 will be a mobile host configured within EURANSIM
		# dnsc4 will be a mobile host configured within EURANSIM
		# dnsc5 will be a mobile host configured within EURANSIM
		# dnsc6 will be a mobile host configured within EURANSIM
		# dnsc7 will be a mobile host configured within EURANSIM
		# dnss will be a mobile host configured within EURANSIM
		# ddoss will be a mobile host configured within EURANSIM
		# ddosc1 will be a mobile host configured within EURANSIM
		# ddosc2 will be a mobile host configured within EURANSIM
		# ddosc3 will be a mobile host configured within EURANSIM
		# ddosc7 will be a mobile host configured within EURANSIM
		# ddosc5 will be a mobile host configured within EURANSIM
		# ddosc4 will be a mobile host configured within EURANSIM
		# ddosc8 will be a mobile host configured within EURANSIM
		# ddosc10 will be a mobile host configured within EURANSIM
		# ddosc6 will be a mobile host configured within EURANSIM
		# ddosc9 will be a mobile host configured within EURANSIM

	info("*** Adding links")
		self.addLink(csr4, csr1, bw=100, delay="10ms", intfName1="csr4-eth2", intfName2="csr1-eth2")
		self.addLink(csr5, csr2, bw=100, delay="10ms", intfName1="csr5-eth3", intfName2="csr2-eth5")
		self.addLink(csr6, csr5, bw=100, delay="10ms", intfName1="csr6-eth3", intfName2="csr5-eth2")
		self.addLink(csr6, csr4, bw=100, delay="10ms", intfName1="csr6-eth4", intfName2="csr4-eth4")
		self.addLink(csr7, csr6, bw=100, delay="10ms", intfName1="csr7-eth2", intfName2="csr6-eth2")
		self.addLink(csr7, csr3, bw=100, delay="10ms", intfName1="csr7-eth4", intfName2="csr3-eth3")
		self.addLink(csr2, csr1, bw=100, delay="10ms", intfName1="csr2-eth3", intfName2="csr1-eth3")
		self.addLink(csr3, csr2, bw=100, delay="10ms", intfName1="csr3-eth4", intfName2="csr2-eth4")
		self.addLink(csr11, csr1, bw=100, delay="10ms", intfName1="csr11-eth2", intfName2="csr1-eth4")
		self.addLink(csr11, csr4, bw=100, delay="10ms", intfName1="csr11-eth3", intfName2="csr4-eth3")
		self.addLink(csr11, dnsc2, bw=100, delay="10ms", intfName1="csr11-eth4", intfName2="dnsc2-eth1")
		self.addLink(csr11, dnsc8, bw=100, delay="10ms", intfName1="csr11-eth10", intfName2="dnsc8-eth1")
		self.addLink(csr11, dnsc10, bw=100, delay="10ms", intfName1="csr11-eth12", intfName2="dnsc10-eth1")
		self.addLink(csr12, csr2, bw=100, delay="10ms", intfName1="csr12-eth2", intfName2="csr2-eth2")
		self.addLink(csr12, csr3, bw=100, delay="10ms", intfName1="csr12-eth4", intfName2="csr3-eth5")
		self.addLink(csr13, csr3, bw=100, delay="10ms", intfName1="csr13-eth2", intfName2="csr3-eth2")
		self.addLink(csr13, csr7, bw=100, delay="10ms", intfName1="csr13-eth3", intfName2="csr7-eth3")
		self.addLink(csr13, ddosc1, bw=100, delay="10ms", intfName1="csr13-eth4", intfName2="ddosc1-eth1")
		self.addLink(csr13, ddosc2, bw=100, delay="10ms", intfName1="csr13-eth5", intfName2="ddosc2-eth1")
		self.addLink(dnsc1, csr11, bw=100, delay="10ms", intfName1="dnsc1-eth1", intfName2="csr11-eth7")
		self.addLink(dnsc9, csr11, bw=100, delay="10ms", intfName1="dnsc9-eth1", intfName2="csr11-eth11")
		self.addLink(dnsc3, csr11, bw=100, delay="10ms", intfName1="dnsc3-eth1", intfName2="csr11-eth13")
		self.addLink(dnsc4, csr11, bw=100, delay="10ms", intfName1="dnsc4-eth1", intfName2="csr11-eth5")
		self.addLink(dnsc5, csr11, bw=100, delay="10ms", intfName1="dnsc5-eth1", intfName2="csr11-eth6")
		self.addLink(dnsc6, csr11, bw=100, delay="10ms", intfName1="dnsc6-eth1", intfName2="csr11-eth8")
		self.addLink(dnsc7, csr11, bw=100, delay="10ms", intfName1="dnsc7-eth1", intfName2="csr11-eth9")
		self.addLink(cgserver, csr7, bw=100, delay="10ms", intfName1="cgserver-eth1", intfName2="csr7-eth5")
		self.addLink(ddoss, csr1, bw=100, delay="10ms", intfName1="ddoss-eth1", intfName2="csr1-eth5")
		self.addLink(ddosc3, csr13, bw=100, delay="10ms", intfName1="ddosc3-eth1", intfName2="csr13-eth6")
		self.addLink(ddosc7, csr13, bw=100, delay="10ms", intfName1="ddosc7-eth1", intfName2="csr13-eth10")
		self.addLink(ddosc5, csr13, bw=100, delay="10ms", intfName1="ddosc5-eth1", intfName2="csr13-eth8")
		self.addLink(ddosc4, csr13, bw=100, delay="10ms", intfName1="ddosc4-eth1", intfName2="csr13-eth7")
		self.addLink(ddosc8, csr13, bw=100, delay="10ms", intfName1="ddosc8-eth1", intfName2="csr13-eth11")
		self.addLink(ddosc10, csr13, bw=100, delay="10ms", intfName1="ddosc10-eth1", intfName2="csr13-eth13")
		self.addLink(ddosc6, csr13, bw=100, delay="10ms", intfName1="ddosc6-eth1", intfName2="csr13-eth9")
		self.addLink(ddosc9, csr13, bw=100, delay="10ms", intfName1="ddosc9-eth1", intfName2="csr13-eth12")

    print(f"\n*** Open5GS: Init 10 subscribers for UE container")
    o5gs   = Open5GS( "172.17.0.2" ,"27017")
    o5gs.removeAllSubscribers()
    with open( prj_folder + "/python_modules/subscriber_profile.json" , 'r') as f:
        profile = json.load( f )
    
    counter = 894
    for _ in range(10):
        counter += 1
        prefix = "001011234567"
        prefix += str(counter)
        profile["imsi"] = prefix
        o5gs.addSubscriber(profile)

    info("\n*** Starting network\n")
    net.start()

    # Fork between CLI and RESTAPI
    processid = os.fork()
    print (" Process ID: " + str(processid))

    if processid >0: # Main process
        mininet_rest = MininetRest(net)
        mininet_rest.run()
        print('INFO:     Main waiting for childs to terminate...')
        time.sleep(2)
        # get all active child processes
        active = active_children()
        # terminate all active children
        for child in active:
            child.kill()
        # block until all children have closed
        for child in active:
            child.join()
        # report active children
        active = active_children()
        print(f'INFO:    Active Children: {len(active)}')
    else:
        time.sleep(2)
        if not AUTOTEST_MODE:
            CLI(net)
        net.stop()
        print("\n*** CTRL+C to terminate\n")