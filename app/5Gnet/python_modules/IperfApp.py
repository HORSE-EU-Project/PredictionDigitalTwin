#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import time , os , json
from datetime import datetime
from docker.models.containers import Container
import redis
from  python_modules.MonitorScenario import MonitorScenario
from  python_modules.UeRanSim import UeRanSim

class IperfApp:
    def __init__( self , mon:MonitorScenario ,  uersim:UeRanSim , apn_mec_name , apn_mec_ip , apn_cld_name, apn_cld_ip ):
        
        self.overall_time = 0
        self.sessions = []
        self.started_sessions = []
        self.uersim = uersim
        self.mon = mon

        self.redis_cli = mon.get_redis_cli()

        # IP and ports associated to the services are hardcoded (for the while)
        self.endpoints = dict()
        self.endpoints["srv_names"] = ["ran","srv_mec1","srv_mec2","srv_cld"]
        for n in self.endpoints["srv_names"]:
            self.endpoints[n]  = dict()

        self.endpoints["ran"]["c_name"] = "ran"
        self.endpoints["ran"]["cont"]   = mon.get_container( "ran" )

        self.endpoints["srv_mec1"]["c_name"]   = "srv_mec1"
        self.endpoints["srv_mec1"]["cont"]     = mon.get_container( "srv_mec1" )
        self.endpoints["srv_mec1"]["apn_name"] = apn_mec_name
        self.endpoints["srv_mec1"]["apn_ip"]   = apn_mec_ip
        self.endpoints["srv_mec1"]["port"]     = [51000] # A list to allow more separated streams, if needed

        self.endpoints["srv_mec2"]["c_name"]   = "srv_mec2"
        self.endpoints["srv_mec2"]["cont"]     = mon.get_container( "srv_mec2" )
        self.endpoints["srv_mec2"]["apn_name"] = apn_mec_name
        self.endpoints["srv_mec2"]["apn_ip"]   = apn_mec_ip
        self.endpoints["srv_mec2"]["port"]     = [52000] # A list to allow more separated streams, if needed

        self.endpoints["srv_cld"]["c_name"]   = "srv_cld"
        self.endpoints["srv_cld"]["cont"]     = mon.get_container( "srv_cld" )
        self.endpoints["srv_cld"]["apn_name"] = apn_cld_name
        self.endpoints["srv_cld"]["apn_ip"]   = apn_cld_ip
        self.endpoints["srv_cld"]["port"]     = [53000] # A list to allow more separated streams, if needed
        
        # TODO: To revise procedure to handle Iperfs sessions with Redis
        # Start IPERF app processes 
        # self.endpoints["ue"]["cont"].exec_run(  cmd="python3 /mnt/volume_util/iperf_ue_app.py"   , detach=True )
        # self.endpoints["mec"]["cont"].exec_run( cmd="python3 /mnt/volume_util/iperf_host_app.py mec" , detach=True )
        # self.endpoints["cld"]["cont"].exec_run( cmd="python3 /mnt/volume_util/iperf_host_app.py cld" , detach=True )

        self.clean_all()
    ##############################################################################

    def wait_until_sessions_finish(self, retry=0.5):
        while self.check_running_iperfs():
            time.sleep(retry)
            

    def check_running_iperfs( self ):
        for key in self.endpoints["srv_names"]:
            top = self.mon.d_client.containers.get( self.endpoints[key]["c_name"] ).top()
            p_names = [p[-1] for p in top['Processes']]
            for p in p_names:
                if "iperf3 " in p:
                    return True
                if "iperf " in p:
                    return True
            return False

    def clean_all( self ):
        self.sessions = []
        self.started_sessions = []
        self.stop_iperf_servers()
        self.stop_iperf_clients()
        self.remove_iperf_logs()

    def reset_sessions(self):
        self.sessions = []
        self.started_sessions = []

    def stop_iperf_clients( self ):
        print( "*** Stop iperf clients" )
        for key in self.endpoints["srv_names"]:
            self.endpoints[key]["cont"].exec_run( cmd="python3 /mnt/volume_util/pskill.py 'iperf3 -c'" , detach=False )

    def stop_iperf_servers( self  ):
        print( "*** Stop iperf servers" )
        for key in self.endpoints["srv_names"]:
            self.endpoints[key]["cont"].exec_run( cmd="python3 /mnt/volume_util/pskill.py 'iperf3 -s'" , detach=False )

    def remove_iperf_logs( self  ):
        matching_files = [file for file in os.listdir("log") if file.startswith("iperf")]
        for f in matching_files: os.remove( "log/"+f )


    def start_session( self, ue_id:int, srv_name:str , sst:str , prot:str , ul_dl:str , bwt:float , t_dur:int , cong_ctrl:str="cubic"):
        # cong_ctrl = <"cubic"|"reno"|"bbr"> --> Set the TCP congestion control algorithm

        apn_name = self.endpoints[srv_name]["apn_name"]
        srv_ip   = self.endpoints[srv_name]["apn_ip"]
        port     = self.endpoints[srv_name]["port"][0]
        cli_ip   = self.uersim.get_ue_address( ue_id , apn=apn_name , sst=sst )
        
        session = dict()
        session["id"] = len( self.sessions )
        session["ue_id"] = ue_id
        session["apn"] = apn_name  # "mec" | "cld"
        session["prot"]  = prot    # "tcp" | "udp"
        session["port"]  = port
        session["ul_dl"] = ul_dl    # "ul"  | "dl"
        session["mbps"]  = bwt
        session["sst"]   = sst
        self.sessions.append( session )

        if cli_ip == None:
            print( f'ERROR: [IperfApp] UE {ue_id} is not connected' )

        if prot == 'udp':
            # Sent IPERF activation message to ue and the channel for the correct service host (distinguished by APN name)
            msgstr = f'{ue_id} {session["id"]} {cli_ip} {srv_ip} {port} {prot} {ul_dl} {bwt} {t_dur}'
            print(f'Starting iperf:{msgstr}')
            self.redis_cli.publish(f'start_iperf_{apn_name}', msgstr )
            self.redis_cli.publish(f'start_iperf_ue', msgstr )

        if prot == 'tcp':
            # convention for outfile: 'iperf_<cli|srv>_s<session_id>_u<ue_id>_<ul|dl>.json'
            srv_file = f'iperf_srv_s{session["id"]}_u{ue_id}_{ul_dl}.json'
            cli_file = f'iperf_cli_s{session["id"]}_u{ue_id}_{ul_dl}.json'
            
            srv_cmd = f'iperf3 -s -B {srv_ip} -1 --interval 1 -p {port} -J --logfile /mnt/log/{srv_file} &'
            cli_cmd = f'iperf3 -c {srv_ip} -B {cli_ip} -p {port} -t {t_dur} -b {bwt}M {ul_dl} -C {cong_ctrl} -J --interval 1 --logfile /mnt/log/{cli_file} &'
            print(f'Starting iperf:{ue_id} {session["id"]} {cli_ip} {srv_ip} {port} {prot} {ul_dl} {bwt} {t_dur}')
            session["t_started"] = time.time() # used only in TCP

            self.endpoints[srv_name]["cont"].exec_run( cmd=srv_cmd , detach=True )
            self.endpoints["ran"]["cont"].exec_run( cmd=cli_cmd , detach=True )


    def parse_redis_udp_results( self , t_start_sim):
        result_keys = ["time", "bwt", "pkt_lost", "pkt_sent", "lost_perc", "latency"]
        for s in self.sessions:
            if s["prot"] != "udp":
                continue
            for k in result_keys:
                s[k] = []
            for sample in self.redis_cli.lrange( f'iperf:udp:{s["id"]}:ue{s["ue_id"]}', 0, -1 ):
                sample_dict = json.loads(sample)
                for k in result_keys:
                    if k == "time":
                        s[k].append(sample_dict[k] - t_start_sim)
                    else:
                        s[k].append(sample_dict[k])
        return self.sessions


    def parse_redis_tcp_results( self , t_start_sim):
        result_keys = ["time", "bwt", "rtt", "retx"]
        # TODO: this is for on-line reporting; currently not feasible with TCP
        #       (iperf3 does not report RTT in stdout and iperf2 causes 100% CPU usage in the client)
        # for s in self.sessions:
        #     if s["prot"] != "tcp":
        #         continue
        #     for k in result_keys:
        #         s[k] = []
        #     tcp_cli = [ json.loads(sample) for sample in self.redis_cli.lrange( f'iperf:tcp_cli:{s["id"]}:ue{s["ue_id"]}', 0, -1 ) ]
        #     tcp_srv = [ json.loads(sample) for sample in self.redis_cli.lrange( f'iperf:tcp_srv:{s["id"]}:ue{s["ue_id"]}', 0, -1 )]
        #     for c in tcp_cli:
        #         s["time"].append( c["time"]-t_start_sim )
        #         s["rtt"].append(  c["rtt"]  )
        #         s["retx"].append( c["retx"] )
        #         while abs(tcp_srv[0]["time"] - c["time"]) > 0.9:
        #             tmp = tcp_srv.pop(0)
        #         if abs(tcp_srv[0]["time"] - c["time"]) < 0.9:
        #             tmp = tcp_srv.pop(0)
        #             s["bwt"].append(tmp["bwt"])

        for s in self.sessions:
            with open( f'log/iperf_cli_s{s["id"]}_u{s["ue_id"]}_{s["ul_dl"]}.json', 'r') as outfile:
                data_cli = json.load( outfile )
            with open( f'log/iperf_srv_s{s["id"]}_u{s["ue_id"]}_{s["ul_dl"]}.json', 'r') as outfile:
                data_srv = json.load( outfile )

            # f = open( f'log/iperf_cli_s{s["id"]}_u{s["ue_id"]}_{s["ul_dl"]}.json' )
            # data_cli = json.load(f)
            # f.close()
            # f = open(f'log/iperf_srv_s{s["id"]}_u{s["ue_id"]}_{s["ul_dl"]}.json')
            # data_srv = json.load(f)
            # f.close()

            tcp_cli=[]
            tcp_srv=[]
            for intervals in data_cli.get( 'intervals' ):
                for ii in intervals.get('streams'):
                    tcp_cli.append({"time" : s["t_started"] + float(ii.get('end') ) ,
                                    "retx" : int(ii.get('retransmits')) , 
                                    "rtt"  : float(ii.get('rtt')) /1e3 
                                    })
                    # s["rtt"].append( float(ii.get('rtt')) /1e3 )
                    # s["retx"].append( int(ii.get('retransmits')) )
                    # s["time_cli"].append( s["t_started"] + float(ii.get('end') ) - t_start_sim )
            for intervals in data_srv.get( 'intervals' ):
                for ii in intervals.get('streams'):
                    tcp_srv.append({"time"  : s["t_started"] + float(ii.get('end') ) ,
                                    "bwt"   : round(float(ii.get('bits_per_second')) )/1e6
                                    })
                    # s["bwt"].append( round(float(ii.get('bits_per_second')) )/1e6 )
                    # s["time_srv"].append( s["t_started"] + float(ii.get('end') ) - t_start_sim )
            for k in result_keys:
                s[k] = []
            for c in tcp_cli:
                s["time"].append( c["time"]-t_start_sim )
                s["rtt"].append(  c["rtt"]  )
                s["retx"].append( c["retx"] )
                while abs(tcp_srv[0]["time"] - c["time"]) > 0.9:
                    tmp = tcp_srv.pop(0)
                if abs(tcp_srv[0]["time"] - c["time"]) < 0.9:
                    tmp = tcp_srv.pop(0)
                    s["bwt"].append(tmp["bwt"])
        return self.sessions

    ### Handle sessions #####################################################################
    # def add_iperf_session( self , ue_id:int , serv_loc_name:str , sst:str , prot:str , port:str , ul_dl:str , bwt:int , t_start , t_dur ):
    #     session = dict()
    #     session["id"] = len( self.sessions )
    #     session["ue_id"] = ue_id
    #     session["serv_loc_name"] = serv_loc_name
    #     session["prot"]  = prot     # "tcp" | "udp"
    #     session["port"]  = port  
    #     session["ul_dl"] = ul_dl    # "ul" | "dl"
    #     session["mbps"]  = bwt
    #     session["sst"]   = sst
    #     session["outfile_srv"]   = "iperf_{}_srv_ue{:n}.iter{:n}.log".format( prot , ue_id , session["id"] )
    #     session["outfile_cli"]   = "iperf_{}_cli_ue{:n}.iter{:n}.log".format( prot , ue_id , session["id"] )
    #     session["t_started"] = 0
    #     session["t_start"]   = t_start
    #     session["t_dur"]     = t_dur
    #     session["bwt_sent"]  = []
    #     session["rtt_sent"]  = []
    #     session["retx_sent"] = []
    #     session["time_sent"] = []
    #     session["bwt_recv"]  = []
    #     session["time_recv"] = []

    #     if t_start + t_dur > self.overall_time:
    #         self.overall_time = t_start+t_dur 

    #     self.sessions.append( session )


    # def check_sessions_to_start( self, cur_time ):
    #     # print( "cur_time={}".format(cur_time) )
    #     for s_id in range( len( self.sessions ) ):
    #         # print( "- check session={}".format(s_id) )
    #         if self.sessions[s_id]["t_start"] <= cur_time:
    #             # print( "- session is to start" )
    #             if s_id not in self.started_sessions:
    #                 # print( "- session is not started yet" )
    #                 self.started_sessions.append(s_id)
    #                 self.start_iperf_session( s_id )


    # def add_and_start_session( self, ue_id:int , serv_loc_name:str , sst:str , prot:str , port:str , ul_dl:str , bwt:int , t_start , t_dur ):
    #     self.add_iperf_session( ue_id , serv_loc_name , sst , prot , port , ul_dl , bwt , t_start , t_dur )
    #     self.start_iperf_session( len(self.sessions)-1 )


    # def start_iperf_session( self , session_id ):
    #     s = self.sessions[session_id]
    #     srv_ip = self.endpoints[ s["serv_loc_name"] ]["apn_ip"]
    #     cli_ip = self.uersim.get_ue_address( s["ue_id"] , apn=s["serv_loc_name"] , sst=s["sst"] )

    #     print( "[" + str(datetime.now().time()) + "] - Start iperf session[{}]: ".format( session_id ) , end="" )
    #     print( " | id: {}".format(self.sessions[session_id]["id"])          , end="" )
    #     print( " | ue_id: {}".format(self.sessions[session_id]["ue_id"])    , end="" )
    #     print( " | srv_ip: {}".format(srv_ip)                               , end="" )
    #     print( " | cli_ip: {}".format(cli_ip) )

    #     self.start_iperf_server( s["serv_loc_name"] , s["prot"] , srv_ip , s["port"] , s["outfile_srv"] )
    #     self.start_iperf_client( cli_ip , srv_ip , s["prot"] ,  s["port"] , s["t_dur"] , s["mbps"] , s["ul_dl"] , s["outfile_cli"] )

    #     self.sessions[session_id]["t_started"] = time.time()


    # def start_iperf_server( self , loc_name:str , prot:str ,  serv_ip:str , port:str , outfile:str ):
    #     # print( "[" + str(datetime.now().time()) + "] - Start iperf server UE " + str(ue_id) + ": " , end="" )
    #     print( "[" + str(datetime.now().time()) + "] - Start iperf server: " , end="" )
    #     print( " | container: " + self.endpoints[loc_name]["c_name"] , end="" )
    #     print( " | server: " + serv_ip                               , end="" )
    #     print( " | port: "   + port                                  , end="" )
    #     print( " | logfile: "   + outfile )

    #     if prot == "tcp":
    #         cmdstr = "iperf3 -s -B " + serv_ip + " -1 --interval 1 -p " + port + " -J --logfile /mnt/log/" + outfile + " &"

    #     elif prot == "udp":
    #         cmdstr = "iperf3 -s -B " + serv_ip + " -1 --interval 1 -p " + port + " -J --logfile /mnt/log/" + outfile + " &"

    #     self.endpoints[loc_name]["cont"].exec_run( cmd=cmdstr , detach=True )


    # def start_iperf_client( self , client_ip:str , serv_ip:str , tcp_udp:str , port:str , duration:int , mbps:int , ul_dl:str, outfile:str=""):

    #     # print( "[" + str(datetime.now().time()) + "] - Start iperf client UE " + str(ue_id) + ": " , end="" )
    #     print( "[" + str(datetime.now().time()) + "] - Start iperf client: " , end="" )
    #     print( " | " + tcp_udp              , end="" )
    #     print( " | server: " + serv_ip       , end="" )
    #     print( " | client: " + client_ip     , end="" )
    #     print( " | port: "   + port          , end="" )
    #     print( " | time: "   + str(duration) , end="" )
    #     print( " | mbps: "   + str(mbps)              )

    #     if ul_dl=="dl":
    #         dl="-R"
    #     else:
    #         dl = ""
    #     if tcp_udp == "tcp":
    #         cmdstr =  "iperf3 -c {} -B {} -p {} -t {} -b {}M {} -J --interval 1 --logfile /mnt/log/{}".format(  serv_ip ,
    #                                                                                                             client_ip , 
    #                                                                                                             port , 
    #                                                                                                             str(duration) ,
    #                                                                                                             str(mbps) ,
    #                                                                                                             dl,
    #                                                                                                             outfile )
    #     elif  tcp_udp == "udp":
    #         cmdstr =  "iperf3 -c {} -B {} -p {} -t {} -b {}M {} -u -J --interval 1 --logfile /mnt/log/{}".format( serv_ip ,
    #                                                                                         client_ip , 
    #                                                                                         port , 
    #                                                                                         str(duration) ,
    #                                                                                         str(mbps) ,
    #                                                                                         dl,
    #                                                                                         outfile )
        
    #     self.endpoints["ue"]["cont"].exec_run( cmd=cmdstr , detach=True )

    #     return time.time()


    # def parse_iperf_files( self , t_start_sim):
        
    #     results = dict()
    #     results["iperf"] = []
        
    #     for s in self.sessions:
    #         filename =  "log/{}".format( s["outfile_cli"] )
    #         f = open(filename)
    #         data_cli = json.load(f)
    #         f.close()
            
    #         filename =  "log/{}".format( s["outfile_srv"] )
    #         f = open(filename)
    #         data_srv = json.load(f)
    #         f.close()

    #         if s["prot"] == "tcp":
    #             if s["ul_dl"] == "dl":
    #                 data1 = data_srv
    #                 data2 = data_cli
    #             else:
    #                 data1 = data_cli
    #                 data2 = data_srv

    #             for intervals in data1.get( 'intervals' ):
    #                 for ii in intervals.get('streams'):
    #                     # iteration["bwt_req"].append( iter_iperf_bwt[it] ) 
    #                     s["bwt_sent"].append( float(ii.get('bits_per_second')) / 1e6 )
    #                     s["rtt_sent"].append( float(ii.get('rtt')) /1e3 )
    #                     s["retx_sent"].append( int(ii.get('retransmits')) )
    #                     s["time_sent"].append( s["t_started"] + float(ii.get('end') ) - t_start_sim )
    #             for intervals in data2.get( 'intervals' ):
    #                 for ii in intervals.get('streams'):
    #                     s["bwt_recv"].append( round(float(ii.get('bits_per_second')) )/1e6 )
    #                     s["time_recv"].append( s["t_started"] + float(ii.get('end') ) - t_start_sim )
    #         # elif prot == "udp":
    #             # if results["ues"][ue_id]["dl"] == True:
    #             #     data1 = data_srv
    #             #     data2 = data_cli
    #             # else:
    #             #     data1 = data_cli
    #             #     data2 = data_srv
    #             # for intervals in data1.get( 'intervals' ):
    #             #     for ii in intervals.get('streams'):
    #             #         results["ues"][ue_id]["bwt_req"].append( iter_iperf_bwt[it] ) 
    #             #         results["ues"][ue_id]["bwt_cli"].append( round(float(ii.get('bits_per_second')) )/1e6 )
    #             #         results["ues"][ue_id]["time_cli"].append( iter_T_start[it]  + float(ii.get('end') ) - start_sim )
    #             # for intervals in data2.get( 'intervals' ):
    #             #     for ii in intervals.get('streams'):
    #             #         results["ues"][ue_id]["bwt_srv"].append( round(float(ii.get('bits_per_second')) )/1e6 )
    #             #         results["ues"][ue_id]["time_srv"].append( iter_T_start[it] + float(ii.get('end') ) - start_sim ) 
    #             #         results["ues"][ue_id]["lost_udp"].append( int(ii.get('lost_packets')) )
    #             #         results["ues"][ue_id]["lost_perc_udp"].append( int(ii.get('lost_percent')) )
            
    #         results["iperf"].append( s )
            
    #     return results["iperf"]
