#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, time, yaml, json, docker, subprocess, shutil
from datetime import datetime
from typing import Tuple

from comnetsemu.cli import CLI, spawnXtermDocker
from comnetsemu.net import Containernet, VNFManager
from comnetsemu.node import APPContainer
from mininet.link import TCLink
from mininet.log import info, setLogLevel
from mininet.node import Controller

def deploy(scenario_file) -> Tuple[Containernet,VNFManager]:

    subprocess.run(["./clean.sh", "log"]) # I want to always restart the environment

    AUTOTEST_MODE = os.environ.get("COMNETSEMU_AUTOTEST_MODE", 0)

    with open( scenario_file, 'r') as f:
        scenario = json.load(f)

    setLogLevel("info")

    net = Containernet(controller=Controller, link=TCLink)
    mgr = VNFManager(net)

    switches = dict()

    ####### Deploy Generic services needed
    global d_client
    d_client = docker.from_env()
    d_client.containers.run( "redislabs/redistimeseries" ,  name="my-redis", ports={"6379/tcp": 6379} , detach=True)

    ####### Deploy the Hosts
    hosts = dict()
    for h in scenario["hosts"]:
        if scenario["hosts"][h]["type"] == "CP":
            hosts[h] = dict()
            hosts[h]["hins"] = add_cp_dockerhost( h , scenario , net )

        if scenario["hosts"][h]["type"] == "MEC":
            hosts[h] = dict()
            hosts[h]["hins"] = add_mec( h , scenario , net , mgr )
            hosts[h]["upfins"] = add_UPFToMec( h+"_upf", h, scenario, mgr )
    
        if scenario["hosts"][h]["type"] == "RAN":
            hosts[h] = dict()
            hosts[h]["hins"] = add_gnb_dockerhost( h , scenario , net )

    ####### Deploy the APPs
    for app in scenario["apps"]:
        add_AppToMec( app, scenario, mgr)

    ####### Create the underlying network
    info("--- Create the underlying network:\n")
    info("Add controller\n")
    net.addController("c0")
    for s in scenario["switches"]:
        switches[s] = net.addSwitch(s)
    for l in scenario["links"]:
        net.addLinkNamedIfce( l["src"]    , l["dst"], bw=l["bwt"] , delay=l["delay"] )
    net.start()

    ####### Start the 5G Control Plane
    info("--- Start 5G Control Plane\n")
    shutil.copy2( scenario_file , "volume_5gc/scenario.json")
    for h in scenario["hosts"]:
        if scenario["hosts"][h]["type"] == "CP":
            hosts[h]["hins"].dins.exec_run( cmd = "python3 /mnt/volume_5gc/init_cp_conf_files.py" , detach=False )
            hosts[h]["hins"].dins.exec_run( cmd = "/mnt/volume_5gc/5gc_start_cp.sh"                , detach=True )
            hosts[h]["hins"].dins.exec_run( cmd = f"python3 /mnt/volume_5gc/init_wait_amf_port_open.py {scenario['hosts'][h]['ip'][0:-3]} {38412}" , detach=False )

    ####### Start the 5G User Plane
    info("--- Start 5G User Plane\n")
    for h in scenario["hosts"]:
        if scenario["hosts"][h]["type"] == "MEC":
            upf_name = h+'_upf'
            host_ip  = scenario['hosts'][h]['ip'][0:-3]

            hosts[h]["hins"].dins.exec_run( 
                cmd=f"bash /mnt/volume_5gc/5gc_init_interfaces.sh {scenario['hosts'][h]['upf']['subnet']}" , detach=False )

            hosts[h]["upfins"].dins.exec_run(
                cmd=f"cp /mnt/volume_5gc/template_upf.yaml  /open5gs/install/etc/open5gs/upf.yaml"     , detach=False )
            cmdstr =  f"bash -c \"sed -i 's|<UPF_NAME>|'{upf_name}'|g'  /open5gs/install/etc/open5gs/upf.yaml\""
            hosts[h]["upfins"].dins.exec_run( cmd=cmdstr , detach=False )
            cmdstr =  f"bash -c \"sed -i 's|<DOCKER_HOST_IP>|'{host_ip}'|g'  /open5gs/install/etc/open5gs/upf.yaml\""
            hosts[h]["upfins"].dins.exec_run( cmd=cmdstr , detach=False )
            cmdstr =  f"bash -c \"sed -i 's|<SUBNET>|'{scenario['hosts'][h]['upf']['subnet']}'|g'  /open5gs/install/etc/open5gs/upf.yaml\""
            hosts[h]["upfins"].dins.exec_run( cmd=cmdstr , detach=False )
            cmdstr =  f"bash -c \"sed -i 's|<DNN>|'{scenario['hosts'][h]['upf']['dnn']}'|g'  /open5gs/install/etc/open5gs/upf.yaml\""
            hosts[h]["upfins"].dins.exec_run( cmd=cmdstr , detach=False )
            cmdstr =  f"bash -c \"sed -i 's|<DEV>|'{scenario['hosts'][h]['upf']['dev']}'|g'  /open5gs/install/etc/open5gs/upf.yaml\""
            hosts[h]["upfins"].dins.exec_run( cmd=cmdstr , detach=False )

            hosts[h]["upfins"].dins.exec_run( cmd=f"./install/bin/open5gs-upfd"     , detach=True )

    ####### Start the 5G RAN
    info("--- Start 5G RAN\n")
    for h in scenario["hosts"]:
        if scenario["hosts"][h]["type"] == "RAN":

            cmdstr =  f"cp /mnt/ueransim/open5gs-gnb_template.yaml  /UERANSIM/build/gnb.yaml"
            hosts[h]["hins"].dins.exec_run( cmd=cmdstr , detach=False )

            cmdstr =  f"bash -c \"sed -i 's|<DOCKER_HOST_IP>|'{scenario['hosts'][h]['ip'][0:-3]}'|g'  /UERANSIM/build/gnb.yaml\""
            hosts[h]["hins"].dins.exec_run( cmd=cmdstr , detach=False )

            cmdstr =  f"bash -c \"sed -i 's|<CP_HOST_IP>|'{scenario['hosts']['cp']['ip'][0:-3]}'|g'  /UERANSIM/build/gnb.yaml\""
            hosts[h]["hins"].dins.exec_run( cmd=cmdstr , detach=False )

            cmdstr =  f"/mnt/ueransim/start_gnb.sh"
            hosts[h]["hins"].dins.exec_run( cmd=cmdstr , detach=True )

    ####### Wait until "is-ngap-up: true"
    time.sleep(0.1)
    for h in scenario["hosts"]:
        if scenario["hosts"][h]["type"] == "RAN":
            iterations = 0
            while True:
                cmdstr = "./nr-cli UERANSIM-gnb-1-1-1 -e status"
                _,out = hosts[h]["hins"].dins.exec_run( cmd=cmdstr , detach=False)
                out = out.decode()
                dct = yaml.safe_load(out)
                reg = dct["is-ngap-up"]
                iterations = iterations + 1
                if reg != True:
                    # print( str(datetime.now().time()) + "gNB ngap is down: is-ngap-up={}".format(reg) )
                    if iterations > 100:
                        print( f"[{str(datetime.now().time())}] gNB ngap is down after 100 checks" )
                        break
                    time.sleep(0.1)
                    continue
                else:
                    print( f"[{str(datetime.now().time())}] gNB ngap is up")
                    break

    return net, mgr


##########################################################################################
##########################################################################################
def add_cp_dockerhost( name:str , scenario:dict , net:Containernet ):
    
    info("*** Adding Host for open5gs {}\n".format(name))
    env={"DB_URI":"mongodb://localhost/open5gs"}
    cp = net.addDockerHost(
        name,
        dimage = scenario["open5gs_image"],
        ip     = scenario["cp_host_ip"],
        dcmd   = "",
        docker_args={
            "environment": env,
            "ports" : { "3000/tcp": 3000 },
            "volumes": {
                scenario["prj_folder"] + "/log": {
                    "bind": "/mnt/log",
                    "mode": "rw",
                },
                scenario["mongodb_folder"]: {
                    "bind": "/var/lib/mongodb",
                    "mode": "rw",
                },
                scenario["prj_folder"] + "/volume_5gc": {
                    "bind": "/mnt/volume_5gc",
                    "mode": "rw",
                },
                scenario["prj_folder"] + "/volume_util": {
                    "bind": "/mnt/volume_util",
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

    num_cpus =  d_client.info()['NCPU']
    cp.dins.update( cpu_period=100000 , cpu_quota=int(100000*num_cpus*scenario["hosts"][name]["cpu_quota"]/100) )

    return cp

##########################################################################################
##########################################################################################
def add_mec( name:str , scenario:dict , net:Containernet , mgr):
    
    mec_par = scenario["hosts"][name]

    info("*** Adding Host for open5gs {}\n".format(name) )
    env={"COMPONENT_NAME":name}
    dh = net.addDockerHost(
        name,
        dimage = scenario["open5gs_image"],
        ip     = mec_par["ip"],
        dcmd   = "",
        docker_args={
            # "cpuset_cpus": mec_par["cpus"],
            # "cpu_period" : 100000, # Default
            # "cpu_quota"  : int(mec_par["cpu_quota"]*100000/100),
            "environment": env,
            "volumes": {
                scenario["prj_folder"] + "/volume_5gc": {
                    "bind": "/mnt/volume_5gc",
                    "mode": "rw",
                },
                scenario["prj_folder"] + "/volume_util": {
                    "bind": "/mnt/volume_util",
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
                "/var/run/docker.sock": {"bind":"/var/run/docker.sock", "mode": "ro"},
            },
            "cap_add": ["NET_ADMIN"],
            "sysctls": {"net.ipv4.ip_forward": 1},
            "devices": "/dev/net/tun:/dev/net/tun:rwm"
        },
    )

    num_cpus =  d_client.info()['NCPU']
    dh.dins.update( cpu_period=100000 , cpu_quota=int(100000*num_cpus*mec_par["cpu_quota"]/100) )

    dh.dins.exec_run( cmd=f'python3 /mnt/volume_util/mon_redis.py' , detach=True )

    return dh

##########################################################################################
##########################################################################################
def add_gnb_dockerhost( name:str , scenario:dict , net:Containernet ):
    info("*** Adding gNB\n")
    env={"COMPONENT_NAME":name}
    h = net.addDockerHost(
        name, 
        dimage = scenario["ueransim_image"],
        ip     = scenario["ran_host_ip"],
        dcmd   = "",
        docker_args={
            # "cpuset_cpus": "0,1",
            "environment": env,
            "volumes": {
                scenario["prj_folder"] + "/volume_ran": {
                    "bind": "/mnt/ueransim",
                    "mode": "rw",
                },
                scenario["prj_folder"] + "/log": {
                    "bind": "/mnt/log",
                    "mode": "rw",
                },
                scenario["prj_folder"] + "/volume_util": {
                    "bind": "/mnt/volume_util",
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

    num_cpus =  d_client.info()['NCPU']
    h.dins.update( cpu_period=100000 , cpu_quota=int(100000*num_cpus*scenario["hosts"][name]["cpu_quota"]/100) )

    return h

##########################################################################################
##########################################################################################
def add_UPFToMec( upf_name:str, mec_name:str, net_param, mgr:VNFManager):
    upf = mgr.addContainer(
        upf_name,
        mec_name,
        dimage = net_param["open5gs_image"],
        dcmd   = "",
        docker_args={
            "environment": {"COMPONENT_NAME":upf_name},
            "volumes": {
                net_param["prj_folder"] + "/log": {
                    "bind": "/mnt/log",
                    "mode": "rw",
                },
                net_param["prj_folder"] + "/volume_5gc": {
                    "bind": "/mnt/volume_5gc",
                    "mode": "rw",
                },
                net_param["prj_folder"] + "/volume_util": {
                    "bind": "/mnt/volume_util",
                    "mode": "rw",
                },
                "/dev/net": {
                    "bind": "/dev/net",
                    "mode": "rw"
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

    return upf

##########################################################################################
##########################################################################################
def add_AppToMec( app_name, scenario , mgr:VNFManager ) -> APPContainer:
    
    app_host  = scenario["apps"][app_name]["host"]
    app_image = scenario["apps"][app_name]["image_name"]

    app = mgr.addContainer( app_name , app_host , app_image , "" , docker_args={
                                    "environment": {"COMPONENT_NAME":app_name},
                                    "volumes": {
                                        scenario["prj_folder"] + "/log": {
                                            "bind": "/mnt/log",
                                            "mode": "rw",
                                        },
                                        scenario["prj_folder"] + "/volume_util": {
                                            "bind": "/mnt/volume_util",
                                            "mode": "rw",
                                        },
                                        "/var/run/docker.sock": {"bind":"/var/run/docker.sock", "mode": "ro"},
                                    } 
                                })

    app.dins.exec_run( cmd=f'python3 /mnt/volume_util/cpu_load_gen.py' , detach=True )
    
    return app


##########################################################################################
##########################################################################################
if __name__ == "__main__":

    AUTOTEST_MODE = os.environ.get("COMNETSEMU_AUTOTEST_MODE", 0)

    scenario_file = sys.argv[1]

    net, mgr = deploy( scenario_file )

    if not AUTOTEST_MODE:
        CLI(net)

    net.stop()
    mgr.stop()
