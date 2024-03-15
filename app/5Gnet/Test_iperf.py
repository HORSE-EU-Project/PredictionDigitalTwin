######################################################
### Test the Environment:
### 
### cld_host: no active services
### mec:host:
###     - srv_mec1: 
###     - srv_mec2: 
###  
######################################################
import time, sys
from  python_modules.UeRanSim import UeRanSim
from  python_modules.Open5GS  import Open5GS
from  python_modules.MonitorScenario  import MonitorScenario
from  python_modules.IperfApp import IperfApp
from  python_modules.Results  import Results


numUEs     = 1

mon    = MonitorScenario()
uersim = UeRanSim(  ["0010100000010{0:0=2d}".format(x+1) for x in range(numUEs)] , "ran" )
iperf  = IperfApp( mon , uersim , apn_mec_name="mec" , apn_mec_ip="10.2.0.1" , apn_cld_name="cld", apn_cld_ip="10.1.0.1" )
o5gs   = Open5GS( mon ,"cp")

cc = "cubic" # Congestion Control = ["cubic"|"reno"|"bbr"]
t_cpu = 20
t_iperf = 20
mec_cpu = 0.375
res    = Results( f'results/ProvaIperf.json' )

# Ensure to clean up 
iperf.clean_all()
mon.clean_redis()
uersim.stop_all_ues()
o5gs.removeAllSubscribers()

# Init subscribers
print(f"*** Open5GS: Adding subscriber for UE 1")
p = o5gs.getProfile_OneUe_maxThr( 100  )
p["imsi"] = uersim.imsi_list[0]
o5gs.addSubscriber(p)

# Init UEs; wait for initialization done
uersim.start_ue( 0 , apn="all", sst="1", sd="1")
uersim.wait_ue_connection_up( 0 , "mec")

# Start Monitors
print(f"*** Start Simulation")

mon.start_all_monitors()

time.sleep(3)

# Test Generate Data Traffic 
iperf.start_session( ue_id=0, srv_name="srv_mec1" , sst="1" , prot="tcp" , ul_dl="ul" , bwt=40 , t_dur=10 , cong_ctrl=cc )
iperf.wait_until_sessions_finish(0.5)

##########################################
# End simulation and collect results
mon.stop_all_monitors()
res.collect_and_save_results( mon.redis_cli, mon, iperf )

