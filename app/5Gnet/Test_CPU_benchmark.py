#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import time, sys, os, json, yaml
import matplotlib.pyplot as plt
import numpy as np
from python_modules.MonitorScenario import MonitorScenario

def main(argv):
    # Linpack()
    PassMark()


##########################################
def PassMark():
    """
    Run a CPU benchmark on the "upf_mec" comntainer using "PassMark" tool
    - It expects the tool to be placed in folder "5gc_config/PerformanceTest". Outputs are in the same folder
    - First deploy the network with test_deployment.py
    """

    mon = MonitorScenario()

    # mon.update_host_resources( h_name="mec_host" , sys_cpu_perc=1 )
    mon._update_container( c_name="mec_host" , cpu_period_in=100000 , cpu_quota_in=100000  )
    mon._update_container( c_name="srv_mec"  , cpu_period_in=100000 , cpu_quota_in=100000  )
    mon._update_container( c_name="upf_mec"  , cpu_period_in=100000 , cpu_quota_in=100000  )
    
    cont = mon.get_container("upf_mec")
    
    # Install dependencies for performance tests
    cmdstr=[]
    cmdstr.append("apt-get update")
    cmdstr.append("apt-get -y install libncurses5")
    cmdstr.append("apt-get -y install libcurl4")
    for c in cmdstr:
        _,out = cont.exec_run( cmd=c , detach=False )
        print( out )
        print( "---------" )

    # Run the tests and save results
    for i in range(10):
        for cpu_quota in [ 37500 ]:

            print("###################################################")
            print("Run CPU TEST with cpu_quota={}".format(cpu_quota))

            # mon.update_host_resources( h_name="mec_host" , sys_cpu_perc=cpu_quota/100000 )
            mon._update_container( c_name="srv_mec"  , cpu_period_in=100000 , cpu_quota_in=cpu_quota  )
            mon._update_container( c_name="upf_mec"  , cpu_period_in=100000 , cpu_quota_in=cpu_quota  )
            mon._update_container( c_name="mec_host" , cpu_period_in=100000 , cpu_quota_in=cpu_quota  )
            
            cmdstr = "/bin/bash /mnt/volume_util/PassMark/run.sh"
            _,o = cont.exec_run( cmd=cmdstr , tty=True , detach=True )

            # Wait process to finish
            time.sleep(1)
            while mon.is_process_running( "upf_mec", "pt_linux_x64"):
                time.sleep(1)
                # print(" .. running...")

            mon._update_container( c_name="mec_host" , cpu_period_in=100000 , cpu_quota_in=100000  )
            mon._update_container( c_name="srv_mec"  , cpu_period_in=100000 , cpu_quota_in=100000  )
            mon._update_container( c_name="upf_mec"  , cpu_period_in=100000 , cpu_quota_in=100000  )
            
            f = open( "results/CPU_benchmark.json" )
            results = json.load(f)
            f.close()

            if str(cpu_quota) not in results.keys():
                results[str(cpu_quota)] = []
            
            f = open( "volume_util/PassMark/results_cpu.yml" )
            data = yaml.safe_load(f)
            f.close()
            results[str(cpu_quota)].append(data)

            with open( "results/CPU_benchmark.json", 'w') as outfile:
                json.dump( results, outfile , indent=2 )
            print(" done.")



##########################################
if __name__ == "__main__":
    main( sys.argv )

