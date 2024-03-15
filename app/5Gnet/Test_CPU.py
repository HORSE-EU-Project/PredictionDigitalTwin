######################################################
### Test running CPU load in the MEC
######################################################
import time, sys
from  python_modules.UeRanSim import UeRanSim
from  python_modules.Open5GS  import Open5GS
from  python_modules.MonitorScenario  import MonitorScenario
from  python_modules.IperfApp import IperfApp
from  python_modules.Results  import Results


mon    = MonitorScenario()
mon.clean_redis()

mon.update_host_resources(h_name="mec_host" , sys_cpu_perc=1 )
mon.update_host_resources(h_name="cld_host" , sys_cpu_perc=1 )

time.sleep(2)

# mon.set_cpu_load( "srv_mec2" , 0.4 )
# mon.set_cpu_load( "srv_cld"  , 0.4 )

# mon.redis_cli.publish('srv_mec2_cpu_stress',"start")
mon.redis_cli.publish('srv_cld_cpu_stress' ,"start")

time.sleep(20)

# mon.set_cpu_load( "srv_mec2" , 0.0 )
# mon.set_cpu_load( "srv_cld"  , 0.0 )
mon.redis_cli.publish('srv_mec2_cpu_stress',"stop")
mon.redis_cli.publish('srv_cld_cpu_stress',"stop")

