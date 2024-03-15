#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import numpy as np
import pandas as pd
from itertools import accumulate
# from python_modules.Monitor import Monitor
# from python_modules.IperfApp import IperfApp

class LoadResults:
    def __init__( self , res_file , load=False):
        self.results = dict()
        self.res_file = res_file
        self.df = pd.DataFrame()
        if load is True:
            self.load_results_and_create_dataframe()

    # def collect_and_save_results( self, redis_cli, mon:Monitor, iperf_app:IperfApp ):
    #     self.get_cpu_results(mon)
    #     self.get_traffic_traces( redis_cli, mon.start_sim)
    #     # self.results["iperf"] = iperf_app.parse_iperf_files(mon.start_sim)
    #     self.results["iperf"] = iperf_app.parse_redis_udp_results(mon.start_sim)
    #     self.results["iperf"] = iperf_app.parse_redis_tcp_results(mon.start_sim)
        
    #     print("*** Save results ...", end = '')
    #     with open( self.res_file, 'w') as outfile:
    #         json.dump( self.results, outfile , indent=2 )
    #     print(" done.")


    def load_results_from_file( self ):
        with open( self.res_file, 'r') as f:
            self.results = json.load(f)

    def load_results_and_create_dataframe( self ):
        with open( self.res_file, 'r') as f:
            self.results = json.load(f)
        self.create_dataframe()

    def create_dataframe( self , force_recalculate=False):
        if (not force_recalculate) and (not self.df.empty):
            return self.df
        for cn in self.results["cpu"]:
            if cn=="sys" or cn=="ue": continue
            df_in = LoadResults.df_from_raw_samples( time=self.results["cpu"][cn]["time"], val=self.results["cpu"][cn]["cpu_perc"], col_name=f'cpu:{cn}' )
            df_in = LoadResults.resample_df_interpolating( df_in )
            self.df = self.df.join( df_in , how='outer' )
        for cn in self.results["traffic"]:
            for itf in self.results["traffic"][cn]:
                df_in = LoadResults.df_from_raw_samples( time=self.results["traffic"][cn]["ogstun_recv"]["time"], val=self.results["traffic"][cn]["ogstun_recv"]["val"], col_name=f'{cn}:{itf}' )
                df_in = LoadResults.resample_df_interpolating( df_in )
                self.df = self.df.join( df_in , how='outer' )

    # Get CPU traces collected by CPUMonitorThread
    # def get_cpu_results( self, mon:Monitor ):
    #     self.results["cpu"] = mon.get_cpu_results()


    ###########################################################
    def get_ue_list_iperf(self):
        ue_list = list(set([ sub["ue_id"] for sub in self.results["iperf"]]))
        return ue_list

    def get_iperf_rawdf(self, kpi="bwt" , ue_id:int=None ):
        """ Returns a df of iperf results; each column identifies an UE/SESSION """
        df = pd.DataFrame()
        for iperf in self.results["iperf"]:
            if iperf["ue_id"] != ue_id and ue_id != None:
                continue
            sid = iperf["id"]
            uid = iperf["ue_id"]
            time = iperf["time"]
            val  = iperf[kpi]
            df1 = LoadResults.df_from_raw_samples(time=time, val=val,col_name=f'iperf:ue{uid}:s{sid}:{kpi}')
            df = df.join( df1, how="outer")
        return df

    def get_iperf_rawdf_collapsed(self, kpi:str, ue_id:int ):
        """ Return a df collapsing all the session for one UEs in one column """
        time=[]
        val=[]
        for iperf in self.results["iperf"]:
            if iperf["ue_id"] is ue_id:
                time.extend( iperf["time"] )
                val.extend( iperf[kpi] )
        df = pd.DataFrame( { f'iperf:ue{ue_id}:{kpi}':val} , index=pd.to_timedelta(time , unit='S') )
        return df

    #################################################################################################
    ### Dataframe generation / manipulation
    @staticmethod
    def df_from_raw_samples( time:list, val:list, col_name:str ):
        df = pd.DataFrame( { f"{col_name}":val} , index=pd.to_timedelta(time , unit='S') )
        return df

    @staticmethod
    def resample_df_interpolating( df ):
        # take a df with multiple columns, rasample it (freq. = seconds) interpolating values
        t = pd.to_timedelta(np.arange( df.index[0].seconds+1 , df.index[-1].seconds+1 ),unit='S')
        union_idx = df.index.union(t)
        df = df.reindex(union_idx)
        df = df.interpolate(method='time', limit_direction='forward', axis=0 , limit_area='inside')
        df = df.loc[(df.index.microseconds==0)]
        return df

    @staticmethod
    def resample_df_nearest( df ):
        # take a df with multiple columns, rasample it (freq. = seconds) taking the nearest value
        df1 = pd.DataFrame()
        for c in df:
            dftmp = df[c].dropna()
            t = pd.to_timedelta(np.arange( dftmp.index[0].seconds+1 , dftmp.index[-1].seconds+1 ), unit='S')
            union_idx = dftmp.index.union(t)
            dftmp = dftmp.reindex(union_idx,method='nearest')
            dftmp = dftmp.loc[(dftmp.index.microseconds==0)]
            df1 = df1.join(dftmp,how="outer")
        return df1

    def df_iperf_bwt( self, ue_id=None):
        # TODO: handle the sum/mean per UE
        df_raw = self.get_iperf_rawdf( kpi="bwt", ue_id=ue_id )
        df1 = LoadResults.resample_df_nearest(df_raw)
        df1_sum  = df1.sum(axis=1)
        df1_mean = df1.mean(axis=1)
        df1_mean.name = "iperf:ue0:bwt:mean"
        df1_sum.name  = "iperf:ue0:bwt:sum"
        # self.df = self.df.join(df1_mean)
        # self.df = self.df.join(df1_sum)
        return df1_sum, df1_mean

    def df_iperf_rtt( self, ue_id=None ):
        # TODO: handle the mean RTT per UE
        df_raw = self.get_iperf_rawdf( kpi="rtt", ue_id=ue_id )
        df1 = LoadResults.resample_df_nearest(df_raw)
        df1_sum  = df1.sum(axis=1)
        df1_mean = df1.mean(axis=1)
        df1_mean.name = "iperf:ue0:rtt:mean"
        # df1_sum.name  = "iperf:ue0:rtt:sum" # Sum does not have any meaning for RTT
        # self.df = self.df.join(df1_mean)
        # self.df = self.df.join(df1_sum)
        return df1_mean

    def df_iperf_retx( self, ue_id=None ):
        # TODO: handle the sum/mean ReTX per UE
        df_raw = self.get_iperf_rawdf( kpi="retx", ue_id=ue_id )
        df1 = LoadResults.resample_df_nearest(df_raw)
        df1_sum  = df1.sum(axis=1)
        df1_mean = df1.mean(axis=1)
        df1_sum.name  = "iperf:ue0:retx:sum"
        df1_mean.name = "iperf:ue0:retx:mean"
        # self.df = self.df.join(df1_mean)
        # self.df = self.df.join(df1_sum)
        return df1_sum, df1_mean

    def stats_tcp_retx( self ):
        df = pd.DataFrame()
        for iperf in self.results["iperf"]:
            df_in = pd.DataFrame( { f'iperf:{iperf["id"]}:ue{iperf["ue_id"]}:retx':list(accumulate(iperf["retx"]))}   , index=pd.to_timedelta(iperf["time"] , unit='S') )
            df = self.join_and_resample_df( df , df_in )
        ue_list = list(set([ sub["ue_id"] for sub in self.results["iperf"]]))
        for ue in ue_list:
            col_list = [s for s in  list(df.columns) if ("iperf:" in s) and (f"ue{ue}:retx" in s) ]
            df[f"iperf_ue{ue}_retx_sum"] = df[col_list].sum(axis=1).values
        return df

