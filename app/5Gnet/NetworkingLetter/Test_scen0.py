#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Testing the Environment

Scenario:
- cld_host: no active services
- mec:host:
    - srv_mec1
    - srv_mec2

Run:
  $ sudo python3 net_deploy.py scenarios/netw_lett.json 
  $ ./NetworkingLetter/Test_scen0.py
"""
import time, sys

sys.path.append(r"/home/vagrant/comnetsemu/app/5Gnet")
__package__ = '5Gnet'

from  python_modules.UeRanSim import UeRanSim
from  python_modules.Open5GS  import Open5GS
from  python_modules.MonitorScenario  import MonitorScenario
from  python_modules.IperfApp import IperfApp
from  python_modules.Results  import Results


def main(argv):

    uersim = UeRanSim(  ["001010000001001"] , "ran" )
    mon    = MonitorScenario()
    iperf  = IperfApp( mon , uersim , apn_mec_name="mec" , apn_mec_ip="10.2.0.1" , apn_cld_name="cld", apn_cld_ip="10.1.0.1" )
    o5gs   = Open5GS( mon, "cp" )

    cc = "cubic" # Congestion Control = ["cubic"|"reno"|"bbr"]
    t_cpu   = 20
    t_iperf = 20
    t_wait  = 10
    mec_cpu = 0.375
    res    = Results( f'results/NewRes_scenario0_tcp_{cc}_cpu{mec_cpu}.json' )

    # Ensure to clean up 
    iperf.clean_all()
    mon.clean_redis()
    uersim.stop_all_ues()
    o5gs.removeAllSubscribers()

    # Start Monitors
    print(f"*** Start Simulation")
    t_start = time.time()
    mon.set_start_time()
    mon.start_all_monitors()

    time.sleep(t_wait)

    # Init subscribers
    print(f"*** Open5GS: Adding subscriber for UE 1")
    p = o5gs.getProfile_OneUe_maxThr( 100  )
    p["imsi"] = uersim.imsi_list[0]
    o5gs.addSubscriber(p)

    time.sleep(t_wait)

    # Init UEs; wait for initialization done
    uersim.start_ue( 0 , apn="all", sst="1", sd="1")
    # uersim.wait_ue_connection_up( 0 , host)

    time.sleep(t_wait)

    # Test Generate CPU
    mon.set_cpu_load( "srv_mec2" , 0.8 )
    time.sleep(t_cpu)
    mon.set_cpu_load( "srv_mec2" , 0.0 )
    mon.update_host_resources(h_name="mec_host",sys_cpu_perc=mec_cpu)
    mon.set_cpu_load( "srv_mec2" , 0.8 )
    time.sleep(t_cpu)
    mon.set_cpu_load( "srv_mec2" , 0.0 )
    mon.update_host_resources(h_name="mec_host",sys_cpu_perc=1)

    time.sleep(t_wait)

    # Test Generate Data Traffic 
    iperf.start_session( ue_id=0, srv_name="srv_mec1" , sst="1" , prot="tcp" , ul_dl="ul" , bwt=40 , t_dur=t_iperf , cong_ctrl=cc )
    iperf.wait_until_sessions_finish(0.5)
    iperf.start_session( ue_id=0, srv_name="srv_mec1" , sst="1" , prot="tcp" , ul_dl="ul" , bwt=50 , t_dur=t_iperf , cong_ctrl=cc )
    iperf.wait_until_sessions_finish(0.5)
    iperf.start_session( ue_id=0, srv_name="srv_mec1" , sst="1" , prot="tcp" , ul_dl="ul" , bwt=60 , t_dur=t_iperf , cong_ctrl=cc )
    iperf.wait_until_sessions_finish(0.5)
    iperf.start_session( ue_id=0, srv_name="srv_mec1" , sst="1" , prot="tcp" , ul_dl="ul" , bwt=70 , t_dur=t_iperf , cong_ctrl=cc )
    iperf.wait_until_sessions_finish(0.5)
    iperf.start_session( ue_id=0, srv_name="srv_mec1" , sst="1" , prot="tcp" , ul_dl="ul" , bwt=80 , t_dur=t_iperf , cong_ctrl=cc )
    iperf.wait_until_sessions_finish(0.5)

    mon.update_host_resources(h_name="mec_host",sys_cpu_perc=mec_cpu)
    time.sleep(t_wait)

    iperf.start_session( ue_id=0, srv_name="srv_mec1" , sst="1" , prot="tcp" , ul_dl="ul" , bwt=40 , t_dur=t_iperf , cong_ctrl=cc )
    iperf.wait_until_sessions_finish(0.5)
    iperf.start_session( ue_id=0, srv_name="srv_mec1" , sst="1" , prot="tcp" , ul_dl="ul" , bwt=50 , t_dur=t_iperf , cong_ctrl=cc )
    iperf.wait_until_sessions_finish(0.5)
    iperf.start_session( ue_id=0, srv_name="srv_mec1" , sst="1" , prot="tcp" , ul_dl="ul" , bwt=60 , t_dur=t_iperf , cong_ctrl=cc )
    iperf.wait_until_sessions_finish(0.5)
    iperf.start_session( ue_id=0, srv_name="srv_mec1" , sst="1" , prot="tcp" , ul_dl="ul" , bwt=70 , t_dur=t_iperf , cong_ctrl=cc )
    iperf.wait_until_sessions_finish(0.5)
    iperf.start_session( ue_id=0, srv_name="srv_mec1" , sst="1" , prot="tcp" , ul_dl="ul" , bwt=80 , t_dur=t_iperf , cong_ctrl=cc )
    iperf.wait_until_sessions_finish(0.5)

    time.sleep(5)

    ##########################################
    # End simulation and collect results
    mon.stop_all_monitors()
    res.collect_and_save_results( mon.redis_cli, mon, iperf )


##########################################################################################
##########################################################################################
if __name__ == "__main__":
    # print( 'Number of arguments:', len(sys.argv), 'arguments.' )
    # print( 'Argument List:', str(sys.argv) )
    main( sys.argv )
