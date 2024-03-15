#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import docker, yaml
import time
from datetime import datetime
from docker.models.containers import Container

class UeRanSim:
    def __init__(self, imsi_list:list , ue_container_name:str ):
        self.imsi_list = imsi_list
        self.num_ues = len(imsi_list)
        self.d_client = docker.from_env()
        self.ue_cont = self.d_client.containers.list(filters={'name':ue_container_name})[0]
        self.ue_status = dict()
        # self.ue_conn   = dict()
        self.ue_status["ue_pid"] = [None]  * self.num_ues
        self.ue_status["ue_reg"] = [False] * self.num_ues


    def stop_all_ues( self ):
        """  Stop all UEs (i.e.: remove nr-ue process) """
        print("[{}] - Stop All UEs:".format(str(datetime.now().time())) )
        self.ue_cont.exec_run( cmd='python3 /mnt/volume_util/pskill.py nr-ue' , detach=False )
        self.ue_status["ue_pid"] = [None]  * self.num_ues
        self.ue_status["ue_reg"] = [False] * self.num_ues


    def stop_ue( self, ue_id:int ):
        """  Stop an UE (i.e.: remove nr-ue process) """

        print("[{}] - Stop UE {:n}:".format(str(datetime.now().time()), ue_id) )

        self.ue_cont.exec_run( cmd=f'python3 /mnt/volume_util/pskill.py open5gs-ue{ue_id}' , detach=False )
        self.ue_status["ue_pid"][ue_id] = None
        self.ue_status["ue_reg"][ue_id] = False


    def start_ue( self, ue_id:int , apn:str="", sst:str="", sd:str=""):
        """  Start an UE (i.e.: start the nr-ue process) """

        imsi = "imsi-{}".format( self.imsi_list[ue_id] )

        print("[{}] - Start UE {:n} | imsi:{} | apn:{}".format(str(datetime.now().time()), ue_id , imsi , apn) )

        if apn == "":
            ue_conf_file_input = "open5gs-ue.yaml"
        elif apn == "all":
            ue_conf_file_input = "open5gs-ue-init-both-pdu.yaml"
        else:
            ue_conf_file_input = "open5gs-ue-init-pdu.yaml"

        ue_conf_file_name = "open5gs-ue{:n}.yaml".format(ue_id)

        cmdstr =  "bash -c \"cp /mnt/ueransim/{} /UERANSIM/config/{}\"".format(ue_conf_file_input,ue_conf_file_name)
        self.ue_cont.exec_run( cmd=cmdstr , detach=False )

        cmdstr =  "bash -c \"sed -i 's|UE_IMSI|'{}'|g' /UERANSIM/config/{}\"".format( imsi , ue_conf_file_name )
        self.ue_cont.exec_run( cmd=cmdstr , detach=False )

        cmdstr =  "bash -c \"sed -i 's|UE_APN|'{}'|g'   /UERANSIM/config/{}\"".format( apn , ue_conf_file_name ) 
        self.ue_cont.exec_run( cmd=cmdstr , detach=False )

        cmdstr =  "bash -c \"sed -i 's|UE_SST|'{}'|g'   /UERANSIM/config/{}\"".format( sst , ue_conf_file_name ) 
        self.ue_cont.exec_run( cmd=cmdstr , detach=False )

        cmdstr =  "bash -c \"sed -i 's|UE_SD|'{}'|g'   /UERANSIM/config/{}\"".format( sd , ue_conf_file_name ) 
        self.ue_cont.exec_run( cmd=cmdstr , detach=False )

        cmdstr =  "bash -c \"/UERANSIM/build/nr-ue -c /UERANSIM/config/{} > /mnt/log/ue{:n}.log 2>&1\"".format(ue_conf_file_name,ue_id)
        self.ue_cont.exec_run( cmd=cmdstr , detach=True )

        # Update PID for new UE
        while True:
            _,out = self.ue_cont.exec_run( cmd="bash -c \"ps -ef | grep nr-ue | grep -v bash | grep open5gs-ue{:n}.yaml\"".format(ue_id) , detach=False )
            out = out.decode()
            if out.count('\n') > 0:
                self.ue_status["ue_pid"][ue_id] = out.split()[1]
                break


    def check_ues_started( self , ue_ids:list ):
        for i in ue_ids:
            _,out = self.ue_cont.exec_run( cmd="bash -c \"ps -ef | grep nr-ue | grep -v bash | grep open5gs-ue{:n}.yaml\"".format(i) , detach=False )
            out = out.decode()
            if out.count('\n') > 0:
                self.ue_stats["ue_pid"][i] = out.split()[1]
            else:
                self.ue_stats["ue_pid"][i] = None
                self.ue_stats["ue_reg"][i] = False


    def check_ues_registration( self ,  ue_ids:list ):
        """ Check the registration of UEs.
            - Updates ue_stats["ue_reg"]
            - Returns the list of UEs that are not RM-REGISTERED."""

        print("[{}] - Check registration for UE ids {}".format(datetime.now().time() , str(ue_ids)) ) 
    
        ue_to_check = []+ue_ids
        ue_not_registered = []

        startime = time.time()

        while len(ue_to_check) > 0:
            for i in ue_to_check:
                if self.ue_status["ue_pid"][i] == None:
                    ue_not_registered.append(i)
                    ue_to_check.remove(i)
                    self.ue_status["ue_reg"][i] = False
                    continue
                cmdstr = "./nr-cli imsi-" + self.imsi_list[i] + " -e status"
                _,out = self.ue_cont.exec_run( cmd=cmdstr , detach=False)
                out = out.decode()
                if out.split()[0] == "ERROR:":
                    self.ue_status["ue_reg"][i] = False
                    ue_not_registered.append(i)
                    ue_to_check.remove(i)
                    continue
                dct = yaml.safe_load(out)
                reg = dct["rm-state"]
                if reg != "RM-REGISTERED":
                    continue
                else:
                    ue_to_check.remove(i)
                    self.ue_status["ue_reg"][i] = True
                    break
            
            if time.time() - startime > 10:
                ue_not_registered = sorted( ue_not_registered + ue_to_check)
                print( "    - After 10 seconds those UEs are not connected {}".format(str(ue_not_registered)) )
                break
        
        return ue_not_registered


    def wait_ue_connection_up( self, ue_id:int , apn:str):
        done = False
        while done == False:
            done = self.check_ue_connection( ue_id , apn )
            # time.sleep(0.1)


    def check_ue_connection( self, ue_id , apn:str  ):
        """
        """
        # print("[{}] - Check UE {} connection to APN {}:".format(datetime.now().time() , str(ue_id) , apn) ) 
        dct = self.get_ps_list( ue_id )
        # print( dct )
        if dct == None:
            return False

        for k,vals in dct.items():
            if vals["apn"] == apn and vals['state']=='PS-ACTIVE':
                return True

        return False


    def get_ps_list( self, ue_id ):
        imsi = "imsi-{}".format( self.imsi_list[ue_id] )
        cmdstr = "./nr-cli " + imsi + " -e ps-list"
        _,out =  self.ue_cont.exec_run( cmd=cmdstr , detach=False)
        dct = yaml.safe_load( out.decode() )
        return dct


    def get_ue_address( self , ue_id , apn:str , sst:str ):
        dct = self.get_ps_list( ue_id )
        if dct == None:
            return None
        for _,vals in dct.items():
            if vals["apn"] == apn and vals['s-nssai']["sst"] == int(sst) and vals["state"]=='PS-ACTIVE':
                return vals["address"]
        return None

    # def connect_ue( self , ue_id:int , sst:str, sd:str, apn:str ):
    #     """ PDU session establishment.
    #         Assumption: no PDU sessions previously established
    #         1- Trigger PDU session establishment
    #         2- Wait until PDU session is established
    #     """
    #     imsi = "imsi-{}".format( self.imsi_list[ue_id] )

    #     if self.ue_status["ue_reg"][ue_id] == False:
    #         print("[{}] - Connecting UE , but UE results not registered -> exit".format( str(datetime.now().time()) ) )
    #         return
        
    #     print("[{}] - Connecting UE {}:".format(str(datetime.now().time()), ue_id) , end='')
        
    #     start = time.time()
    #     cmdstr = "./nr-cli " + imsi + " -e \"ps-establish IPv4 --sst " + sst + " --sd " + sd + " --dnn " + apn +"\""

    #     _,out = self.ue_cont.exec_run( cmd=cmdstr , detach=True)
    #     time.sleep(0.5)

    #     address = ""

    #     cmdstr = "./nr-cli " + imsi  + " -e ps-list"

    #     end = time.time()
    #     elapsed = end-start
    #     print( " | setup time = {:.3f}".format(elapsed)  , end='')
    #     print( " | UE address: " + address )

    #     self.ue_status["ue_pdu_ip"][ue_id] = address
    #     # return address


    # def reconnect_ue( ue_id:int, ue:Container, sst:str, sd:str, apn:str , sim_par:dict ):
    #     #           ( ue_id:int, ue:Container, imsi:str, sst:str, sd:str, apn:str ):
    #     """ 1- Release all PDU sessions
    #         2- wait for all PDU session removed
    #         3- Call ue_connect
    #     """
    #     print("[{}] - Re-connecting UE {}:".format(str(datetime.now().time()), ue_id))
        
    #     start = time.time()
    #     cmdstr = "./nr-cli " + sim_par["imsi"][ue_id] + " -e \"ps-release-all\""
    #     _,out = ue.exec_run( cmd=cmdstr , detach=False)

    #     # Wait for PDU deletion
    #     # time.sleep(0.1)

    #     address = ""

    #     cmdstr = "./nr-cli " + sim_par["imsi"][ue_id] + " -e status"

    #     print("[{}] - PDU session released for UE {}:".format(str(datetime.now().time()), ue_id))


    #     #####################################################
    #     address = connect_ue( ue_id, ue, sst, sd, apn , sim_par )

    #     return address






#####################################################
#####################################################
### OLD FUNCTINS FOR UERANSIM v3.1.9

# def stop_ue( ue_id:int , ue:Container , sim_par:dict , ue_stats:dict ):
#     """  Stop an UE (i.e.: remove nr-ue process) """

#     print("[{}] - Stop UE {:n}:".format(str(datetime.now().time()), ue_id) )

#     _,out=ue.exec_run( cmd="bash -c \"ps -ef | grep nr-ue | grep -v bash | grep open5gs-ue{:n}.yaml\"".format(ue_id) , detach=False )
#     out = out.decode()
#     out = out.split('\n')
#     for k in range(0, len(out)-1 ):
#         pid = out[k].split()[1]
#         ue.exec_run( cmd="bash -c \"kill {}\"".format(pid) , detach=False )
#         ue_stats["ue_pid"][ue_id] = None
#         ue_stats["ue_reg"][ue_id] = False
#         ue_stats["ue_pdu_ip"][ue_id] = None


# def start_ue( ue_id:int , ue:Container , imsi:str , ue_stats:dict() , apn:str="", sst:str="", sd:str=""):
#     """  Start an UE (i.e.: start the nr-ue process) """

#     print("[{}] - Start UE {:n} | imsi:{} | apn:{}".format(str(datetime.now().time()), ue_id , imsi , apn) )

#     if apn == "":
#         ue_conf_file_input = "open5gs-ue.yaml"
#     elif apn == "all":
#         ue_conf_file_input = "open5gs-ue-init-both-pdu.yaml"
#     else:
#         ue_conf_file_input = "open5gs-ue-init-pdu.yaml"

#     ue_conf_file_name = "open5gs-ue{:n}.yaml".format(ue_id)

#     cmdstr =  "bash -c \"cp /mnt/ueransim/{} /UERANSIM/config/{}\"".format(ue_conf_file_input,ue_conf_file_name)
#     ue.exec_run( cmd=cmdstr , detach=False )

#     cmdstr =  "bash -c \"sed -i 's|UE_IMSI|'{}'|g' /UERANSIM/config/{}\"".format( imsi , ue_conf_file_name )
#     ue.exec_run( cmd=cmdstr , detach=False )

#     cmdstr =  "bash -c \"sed -i 's|UE_APN|'{}'|g'   /UERANSIM/config/{}\"".format( apn , ue_conf_file_name ) 
#     ue.exec_run( cmd=cmdstr , detach=False )

#     cmdstr =  "bash -c \"sed -i 's|UE_SST|'{}'|g'   /UERANSIM/config/{}\"".format( sst , ue_conf_file_name ) 
#     ue.exec_run( cmd=cmdstr , detach=False )

#     cmdstr =  "bash -c \"sed -i 's|UE_SD|'{}'|g'   /UERANSIM/config/{}\"".format( sd , ue_conf_file_name ) 
#     ue.exec_run( cmd=cmdstr , detach=False )

#     cmdstr =  "bash -c \"/UERANSIM/build/nr-ue -c /UERANSIM/config/{} > /mnt/log/ue{:n}.log 2>&1\"".format(ue_conf_file_name,ue_id)
#     ue.exec_run( cmd=cmdstr , detach=True )

#     # Update PID for new UE
#     while True:
#         _,out=ue.exec_run( cmd="bash -c \"ps -ef | grep nr-ue | grep -v bash | grep open5gs-ue{:n}.yaml\"".format(ue_id) , detach=False )
#         out = out.decode()
#         if out.count('\n') > 0:
#             ue_stats["ue_pid"][ue_id] = out.split()[1]
#             break


# def check_ues_started( ue_ids:list , ue:Container , sim_par:dict , ue_stats:dict ):
    
#     for i in ue_ids:
#         _,out=ue.exec_run( cmd="bash -c \"ps -ef | grep nr-ue | grep -v bash | grep open5gs-ue{:n}.yaml\"".format(i) , detach=False )
#         out = out.decode()
#         if out.count('\n') > 0:
#             ue_stats["ue_pid"][i] = out.split()[1]
#         else:
#             ue_stats["ue_pid"][i] = None
#             ue_stats["ue_reg"][i] = False
#             ue_stats["ue_pdu_ip"][i] = None


# def check_ues_registration( ue_ids:list , ue:Container , sim_par:dict , ue_stats:dict ):
#     """ Check the registration of UEs.
#         - Updates ue_stats["ue_reg"]
#         - Returns the list of UEs that are not RM-REGISTERED."""

#     print("[{}] - Check registration for UE ids {}".format(datetime.now().time() , str(ue_ids)) ) 
   
#     ue_to_check = []+ue_ids
#     ue_not_registered = []

#     startime = time.time()

#     while len(ue_to_check) > 0:
#         for i in ue_to_check:
#             if ue_stats["ue_pid"][i] == None:
#                 ue_not_registered.append(i)
#                 ue_to_check.remove(i)
#                 ue_stats["ue_reg"][i] = False
#                 continue
#             cmdstr = "./nr-cli " + sim_par["imsi"][i] + " -e status"
#             _,out = ue.exec_run( cmd=cmdstr , detach=False)
#             out = out.decode()
#             if out.split()[0] == "ERROR:":
#                 ue_stats["ue_reg"][i] = False
#                 ue_not_registered.append(i)
#                 ue_to_check.remove(i)
#                 continue
#             dct = yaml.safe_load(out)
#             reg = dct["rm-state"]
#             if reg != "RM-REGISTERED":
#                 continue
#             else:
#                 ue_to_check.remove(i)
#                 ue_stats["ue_reg"][i] = True
#                 break
        
#         if time.time()-startime > 10:
#             ue_not_registered = sorted( ue_not_registered + ue_to_check)
#             print( "    - After 10 seconds those UEs are not connected {}".format(str(ue_not_registered)) )
#             break
    
#     return ue_not_registered

# ##########################################################################################################
# def check_ue_connection( ue_id , ue:Container , imsi:str  , ue_stats:dict  ):
#     # print("*** Check UE connection for id {}:".format(str(ue_id)) )

#     image_name = ue.image.tags[0].split(":")[0]

#     if image_name == "myueransim_v3-1-9":
#         cmdstr = "./nr-cli " + imsi + " -e status"
#         _,out = ue.exec_run( cmd=cmdstr , detach=False)
#         if out.split()[0] == "ERROR:":
#             print(" - ERROR: Checking UE connection, this UE was not found: id=" + str(ue_id) + " | imsi=" + imsi )
#         dct = yaml.safe_load(out.decode())
#         pdus = dct["pdu-sessions"]
#         if pdus==None:
#             ue_stats["ue_pdu_ip"][ue_id] = None
#             return False
#         else:
#             pdu = dct["pdu-sessions"][0]
#             ue_stats["ue_pdu_ip"][ue_id] = pdu["address"]
#             return True

#     elif  image_name == "myueransim_v3-2-6":
#         cmdstr = "./nr-cli " + imsi + " -e ps-list"
#         _,out = ue.exec_run( cmd=cmdstr , detach=False)
#         out = out.decode()
#         if len( out.split() ) == 0:
#             return False
#         elif out.split()[0] == "ERROR:":
#             print(" - ERROR: Checking UE connection, this UE was not found: id=" + str(ue_id) + " | imsi=" + imsi )
#             return False
#         else:
#             dct = yaml.safe_load( out )
#             firstpdu = list(dct.keys())[0]
#             if dct[firstpdu]["address"] == None:
#                 ue_stats["ue_pdu_ip"][ue_id] = None
#                 ue_stats["ue_apn"][ue_id]    = None
#                 ue_stats["ue_sst"][ue_id]    = None
#                 ue_stats["ue_sd"][ue_id]     = None
#                 return False
#             else:
#                 ue_stats["ue_pdu_ip"][ue_id] = dct[firstpdu]["address"]
#                 ue_stats["ue_apn"][ue_id]    = dct[firstpdu]["apn"]
#                 ue_stats["ue_sst"][ue_id]    = dct[firstpdu]["s-nssai"]["sst"]
#                 ue_stats["ue_sd"][ue_id]     = dct[firstpdu]["s-nssai"]["sd"]
#                 return True
#     else:
#         print( "Error: undefined UERANSIM image: {}".format(image_name) )
#         return False

# def check_ues_connection( ue_ids:list , ue:Container , sim_par:dict , ue_stats:dict ):
#     """ Check the connection of UEs.
#         - Returns the list of UEs that are not connected (i.e., no IP assigned)."""

#     print("[{}] - Check connection for UE ids {}".format(datetime.now().time() , str(ue_ids)) ) 
   
#     ue_to_check = []+ue_ids
#     ue_not_connected = []

#     startime = time.time()

#     while len(ue_to_check) > 0:
#         for i in ue_to_check:
#             if check_ue_connection( i , ue , sim_par["imsi"][i]  , ue_stats  ) == True:
#                 ue_to_check.remove(i)
        
#         if time.time()-startime > 10:
#             ue_not_connected = sorted( ue_not_connected + ue_to_check)
#             print( "    - After 10 seconds those UEs are not connected {}".format(str(ue_not_connected)) )
#             break
    
#     return ue_not_connected


# def connect_ue( ue_id:int, ue:Container, sst:str, sd:str, apn:str , imsi:str , ue_stats:dict ):
#     """ PDU session establishment.
#         Assumption: no PDU sessions previously established
#         1- Trigger PDU session establishment
#         2- Wait until PDU session is established
#     """
#     if ue_stats["ue_reg"][ue_id] == False:
#         print("[{}] - Connecting UE , but UE results not registered -> exit".format( str(datetime.now().time()) ) )
#         return
    
#     print("[{}] - Connecting UE {}:".format(str(datetime.now().time()), ue_id) , end='')
    
#     start = time.time()
#     cmdstr = "./nr-cli " + imsi + " -e \"ps-establish IPv4 --sst " + sst + " --sd " + sd + " --dnn " + apn +"\""

#     _,out = ue.exec_run( cmd=cmdstr , detach=True)
#     time.sleep(0.5)

#     address = ""
#     image_name = ue.image.tags[0].split(":")[0]

#     #####################################################
#     if image_name == "myueransim_v3-1-9":
#         cmdstr = "./nr-cli " + imsi + " -e status"
#         while True:
#             _,out = ue.exec_run( cmd=cmdstr , detach=False)
#             out = out.decode()
#             dct = yaml.safe_load(out)
#             pdus = dct["pdu-sessions"]
#             if pdus==None:
#                 continue
#             else:
#                 pdu = dct["pdu-sessions"][0]
#                 address = pdu["address"]
#                 break

#     #####################################################
#     elif image_name == "myueransim_v3-2-6" or \
#          image_name == "myueransim_latest":
#         cmdstr = "./nr-cli " + imsi  + " -e ps-list"

#     #####################################################
#     else:
#         print( "Error: undefined UERANSIM image: {}".format(image_name) )

#     end = time.time()
#     elapsed = end-start
#     print( " | setup time = {:.3f}".format(elapsed)  , end='')
#     print( " | UE address: " + address )

#     ue_stats["ue_pdu_ip"][ue_id] = address
#     # return address


# def reconnect_ue( ue_id:int, ue:Container, sst:str, sd:str, apn:str , sim_par:dict ):
#     #           ( ue_id:int, ue:Container, imsi:str, sst:str, sd:str, apn:str ):
#     """ 1- Release all PDU sessions
#         2- wait for all PDU session removed
#         3- Call ue_connect
#     """
#     print("[{}] - Re-connecting UE {}:".format(str(datetime.now().time()), ue_id))
    
#     start = time.time()
#     cmdstr = "./nr-cli " + sim_par["imsi"][ue_id] + " -e \"ps-release-all\""
#     _,out = ue.exec_run( cmd=cmdstr , detach=False)
#     # time.sleep(0.1)

#     # Wait for PDU deletion
#     address = ""
#     image_name = ue.image.tags[0].split(":")[0]

#     #####################################################
#     if image_name == "myueransim_v3-1-9":
#         cmdstr = "./nr-cli " + sim_par["imsi"][ue_id] + " -e status"
#         while True:
#             _,out = ue.exec_run( cmd=cmdstr , detach=False)
#             out = out.decode()
#             dct = yaml.safe_load(out)
#             pdus = dct["pdu-sessions"]
#             if pdus==None:
#                 break
#             else:
#                 pdu = dct["pdu-sessions"][0]
#                 address = pdu["address"]
#                 continue

#     #####################################################
#     elif image_name == "myueransim_v3-2-6" or \
#          image_name == "myueransim_latest":

#         cmdstr = "./nr-cli " + sim_par["imsi"][ue_id] + " -e status"
    
#     #####################################################
#     else:
#         print( "Error: undefined UERANSIM image: {}".format(image_name) )

#     print("[{}] - PDU session released for UE {}:".format(str(datetime.now().time()), ue_id))


#     #####################################################
#     address = connect_ue( ue_id, ue, sst, sd, apn , sim_par )

#     return address


