######################################################
### Scenario deployed
### - cld_host:
###   - oxys_srv_cld --> APPContainer running twamp server
### - mec_host:
###   - oxys_srv_mec --> APPContainer running twamp server
### - ue
###   - oxys_cli --> APPContainer running twamp server
### 
### How to run the example:
### 1. Deploy the scenario and start the script
###     $ sudo python3 net_deploy.py scenarios/oxys.json
###     $ python3 Test_oxys.py
###
### 2. Start the script deploying the scenario:
###     $ sudo python3 Test_oxys.py scenarios/oxys.json
######################################################
import time, sys, docker, subprocess

from docker.models.containers import Container

from net_deploy import deploy
from python_modules.UeRanSim import UeRanSim
from  python_modules.MonitorScenario  import MonitorScenario
from python_modules.Open5GS  import Open5GS

def main(argv):

    if len(sys.argv) > 1:
        deploy( sys.argv[1] )

    mon    = MonitorScenario()
    o5gs   = Open5GS( mon ,"cp")
    uersim = UeRanSim(  ["001010000001001"] , "ran" )
    
    # Retrieve the containers
    docker_client = docker.from_env()
    oxys_srv_cld = docker_client.containers.get("oxys_srv_cld")
    oxys_srv_mec = docker_client.containers.get("oxys_srv_mec")
    oxys_cli     = docker_client.containers.get("oxys_cli")

    # (Re)-start OXYS server
    oxys_srv_cld.exec_run( cmd='pkill ./twamp.py' , detach=False )
    oxys_srv_mec.exec_run( cmd='pkill ./twamp.py' , detach=False )

    oxys_srv_cld.exec_run( cmd=f'python3 ./twamp.py responder 0.0.0.0:861' , detach=True )
    oxys_srv_mec.exec_run( cmd=f'python3 ./twamp.py responder 0.0.0.0:861' , detach=True )

    # Init subscribers
    o5gs.removeAllSubscribers()
    print(f"*** Open5GS: Adding subscriber for UE 1")
    p = o5gs.getProfile_OneUe_maxThr( 100  )
    p["imsi"] = uersim.imsi_list[0]
    o5gs.addSubscriber(p)

    time.sleep(1)

    # # (Re)-start the UE
    uersim.stop_all_ues()
    uersim.start_ue( 0 , apn="all", sst="1", sd="1")
    uersim.wait_ue_connection_up( 0 , "mec")
    mec_outbound_ip = uersim.get_ue_address( 0 , apn="mec" , sst="1")
    cld_outbound_ip = uersim.get_ue_address( 0 , apn="cld" , sst="1")

    # Run TWAMP test toward the 'far' and 'near' MECs
    print( "Perform twamp test on the ''far'' MEC" )
    text = oxys_cli.exec_run( cmd=f'python3 ./twamp.py sender 10.1.0.1:861 {cld_outbound_ip}:861' , detach=False )
    print( text.output.decode("utf-8") )

    print( "Perform twamp test to the ''near'' MEC" )
    text = oxys_cli.exec_run( cmd=f'python3 ./twamp.py sender 10.2.0.1:861 {mec_outbound_ip}:861' , detach=False )
    print( text.output.decode("utf-8") )


##########################################################################################
if __name__ == "__main__":
    main( sys.argv )
