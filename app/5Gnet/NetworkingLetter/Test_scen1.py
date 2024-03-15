#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test throughput VS. MEC resource usage

Scenario:
- cld_host: no active services
- mec_host:
    - srv_mec1: receives from ue0 traffic from 10 to 70 Mbps
    - srv_mec2: no actions

Run:
  $ sudo python3 net_deploy.py scenarios/netw_lett.json 
  $ ./NetworkingLetter/Test_scen1.py
"""

import time, sys

sys.path.append(r"/home/vagrant/comnetsemu/app/5Gnet")
__package__ = '5Gnet'

from  python_modules.UeRanSim import UeRanSim
from  python_modules.Open5GS  import Open5GS
from  python_modules.MonitorScenario  import MonitorScenario
from  python_modules.IperfApp import IperfApp
from  python_modules.Results  import Results


for h in [0.2, 0.375, 0.7, 1]:

    cc = "cubic" # Congestion Control = ["cubic"|"reno"|"bbr"]
    max_thr = 100
    res_file = f'results/Res_scen1b_tcp_{cc}_hostcpu{h}.json'

    uersim = UeRanSim(  ["001010000001001"] , "ran" )
    mon    = MonitorScenario()
    iperf  = IperfApp( mon , uersim , apn_mec_name="mec" , apn_mec_ip="10.2.0.1" , apn_cld_name="cld", apn_cld_ip="10.1.0.1" )
    o5gs   = Open5GS( "172.17.0.2" ,"27017")

    # Ensure to clean up 
    iperf.clean_all()
    mon.clean_redis()
    uersim.stop_all_ues()
    o5gs.removeAllSubscribers()

    # Init subscribers
    print(f"*** Open5GS: Adding subscriber for UE 1")
    p = o5gs.getProfile_OneUe_maxThr( max_thr  )
    p["imsi"] = uersim.imsi_list[0]
    o5gs.addSubscriber(p)

    uersim.start_ue( 0 , apn="all", sst="1", sd="1")
    uersim.wait_ue_connection_up( 0 , "mec")

    mon.update_host_resources(h_name="mec_host",sys_cpu_perc=h)

    # Start simulation
    t_start = time.time()
    mon.set_start_time()
    mon.start_all_monitors()

    bitrates=[]
    if h == 1:
        bitrates = [10,20,30,40,50,60,70,80,90]
    if h == 0.7:
        bitrates = [10,20,30,40,50,60,70,80,90]
    if h == 0.375:
        bitrates = [10,20,30,40,50,60,70]
    if h == 0.2:
        bitrates = [10,20,30,40,50]

    for b in bitrates:
        iperf.start_session( ue_id=0, srv_name="srv_mec1" , sst="1" , prot="tcp" , ul_dl="ul" , bwt=b , t_dur=20 , cong_ctrl=cc )
        iperf.wait_until_sessions_finish(0.5)

    ##########################################
    # End simulation and collect results
    mon.stop_all_monitors()
    res    = Results( res_file )
    res.collect_and_save_results( mon.redis_cli, mon, iperf )

