#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test coexistance of throughput intensive and CPU intensive APPs

Scenario:
- cld_host: no active services
- mec:host:
    - srv_mec1: Receives 40 Mbps from UE
    - srv_mec2: Generates CPU load from 0 to 90% of the overall MEC CPU

Run:
  $ sudo python3 net_deploy.py scenarios/netw_lett.json 
  $ ./NetworkingLetter/Test_scen2.py
"""

import time, sys

sys.path.append(r"/home/vagrant/comnetsemu/app/5Gnet")
__package__ = '5Gnet'

from  python_modules.UeRanSim import UeRanSim
from  python_modules.Open5GS  import Open5GS
from  python_modules.MonitorScenario  import MonitorScenario
from  python_modules.IperfApp import IperfApp
from  python_modules.Results  import Results


host_cpu_perc = [0.2, 0.375, 0.7, 1 ]
# iperf_bwt     = [40 , 40   , 40 , 40]    ## Scenario 2a
iperf_bwt     = [50 , 70   , 90 , 90]    ## Scenario 2b

for i in [0,1,2,3]:

    cc = "cubic" # Congestion Control = ["cubic"|"reno"|"bbr"]
    max_thr = 100
    res_file = f'results/Res_scen2b_tcp_{cc}_hostcpu{host_cpu_perc[i]}.json'


    time_interval = 30 # seconds
    srv_mec_cpu = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

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

    mon.update_host_resources(h_name="mec_host",sys_cpu_perc=host_cpu_perc[i])
    
    time.sleep(1)

    ##########################################
    # Start simulation
    t_start = time.time()
    mon.set_start_time()
    mon.start_all_monitors()

    iperf.start_session( ue_id=0, srv_name="srv_mec1" , sst="1" , prot="tcp" , ul_dl="ul" , bwt=iperf_bwt[i] , t_dur=len(srv_mec_cpu)*time_interval+time_interval , cong_ctrl=cc )
    for load in srv_mec_cpu:
        time.sleep(time_interval)
        mon.set_cpu_load( "srv_mec2" , load )
        print( f"Set srv_mec2 CPU load to {load*100}%" )
    iperf.wait_until_sessions_finish()

    ##########################################
    # End simulation and collect results
    mon.stop_all_monitors()
    res    = Results( res_file )
    res.collect_and_save_results( mon.redis_cli, mon, iperf )
