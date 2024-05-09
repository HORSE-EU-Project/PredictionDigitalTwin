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

import os

from comnetsemu.cli import CLI
from comnetsemu.net import Containernet, VNFManager
from mininet.link import TCLink
from mininet.log import info, setLogLevel
from mininet.node import OVSKernelSwitch, Controller, RemoteController

from python_modules.Open5GS   import Open5GS

from mininetFastAPI.mininetFastAPI import MininetRest

import json, time, os
from multiprocessing import Process, active_children

from subprocess import PIPE, Popen

def cmdline(command):
    process = Popen(
        args=command,
        stdout=PIPE,
        shell=True
    )
    return

if __name__ == "__main__":

    AUTOTEST_MODE = os.environ.get("COMNETSEMU_AUTOTEST_MODE", 0)

    setLogLevel("info")

    script_path = os.path.abspath(__file__)
    prj_folder = os.path.dirname(script_path)

    # prj_folder="/home/vagrant/comnetsemu/app/comnetsemu_5Gnet"
    mongodb_folder="/home/vagrant/mongodbdata"

    # Uncomment to link to sFlow (but first run start.sh script to activate sFlow deamon
    print("*** Starting sFlow\n")
    cmdline("./sflow-rt/start.sh &")
    time.sleep(5)
    exec(open('./sflow-rt/extras/sflow.py').read())
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
        # dimage="myueransim_v3-2-6",
        dimage="ue_enhanced",
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

    dns_s = net.addDockerHost('dns_s', dimage="dev_test", ip="192.168.0.200/24", docker_args={"hostname": "dns_server"})
    internet_server = net.addDockerHost('internet_server', dimage="dev_test",  ip="192.168.0.201/24", docker_args={"hostname": "internet_server"})


    info("*** Add remote controller\n")
    c0 = RemoteController( 'c0', ip='127.0.0.1', port=6653 )
    net.addController( c0 )

    info("*** Adding switch\n")
    ceos0 = net.addSwitch("ceos0")
    ceos1 = net.addSwitch("ceos1")
    ceos2 = net.addSwitch("ceos2")

    info("*** Adding links\n")
    net.addLink(ceos0, ceos1, bw=100, delay="10ms", intfName1="ceos0-eth1", intfName2="ceos1-eth1")
    net.addLink(ceos1, ceos2, bw=100, delay="10ms", intfName1="ceos1-eth2", intfName2="ceos2-eth1")

    net.addLink(cp,      ceos1, bw=1000, delay="1ms", intfName1="cp-eth1",  intfName2="ceos1-eth4")
    net.addLink(upf,     ceos1, bw=1000, delay="1ms", intfName1="upf-eth1",  intfName2="ceos1-eth3")

    net.addLink(dns_s, ceos2, bw=100, delay="1ms", intfName1="dns-s-eth1",  intfName2="ceos2-eth3")
    net.addLink(internet_server, ceos2, bw=100, delay="50ms", intfName1="internet-eth1", intfName2="ceos2-eth4")

    net.addLink(ue,  ceos0, bw=1000, delay="1ms", intfName1="ue-s1",  intfName2="s1-ue")
    net.addLink(gnb, ceos0, bw=1000, delay="1ms", intfName1="gnb-s1", intfName2="s1-gnb")

    info("\n*** Starting network\n")
    net.start()
    
    info("\n*** Checking network connectivity\n")
    net.pingAll()

    info("\n*** Registering mobile UEs...\n")

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

    #info("\n*** Starting network\n")
    #net.start()

    print("\n*** Waiting for 5G GTP connections to be instantiated...")
    cmdline("./5g_wait_for_healthy.sh")

    print("\n*** Checking network connectivity\n")
    net.pingAll()

    # Fork between CLI and RESTAPI
    processid = os.fork()
    print (" Process ID: " + str(processid))

    if processid > 0: # Main process
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
        print(f'INFO:     Active Children: {len(active)}')
    else:
        time.sleep(2)
        if not AUTOTEST_MODE:
            #info("*** Waiting 1 min. for configuration to be finalized...\n")
            #time.sleep(60)
            #net.pingAll()
            CLI(net)
        net.stop()
        print("\n*** CTRL+C to terminate\n")

