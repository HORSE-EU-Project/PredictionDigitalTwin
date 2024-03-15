#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import json, itertools
from itertools import accumulate

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from numpy import arange


def get_color_list( type="default"):
    if type == "default":
        prop_cycle = plt.rcParams['axes.prop_cycle']
        return prop_cycle.by_key()['color']
    if type == "base":
        return list(mcolors.BASE_COLORS.values())

def movingaverage(interval, window_size):
    window= np.ones(int(window_size))/float(window_size)
    return np.convolve(interval, window, 'same')

def fitting_scatter_plot(df:pd.DataFrame, x_column, y_column, x_lim=None, polyorder=2):
    dftmp = df.dropna(axis=0, how='any', thresh=None, subset=[x_column,y_column], inplace=False)
    if x_lim is not None:
        dftmp = dftmp[dftmp[x_column] > x_lim[0]]
        dftmp = dftmp[dftmp[x_column] < x_lim[1]]
    x = dftmp[x_column].values
    y = dftmp[y_column].values

    p = np.polyfit(x , y, polyorder)
    x_line = arange( min(x), max(x), 1 )
    y_line = np.polyval(p, x_line)
    
    return x_line, y_line


def get_plot_info( idx=1, colors=None ):
    if colors is None:  colors = get_color_list()
    if idx == 1:
        c_names = [     "ran" , "mec_host" , "mec_host_upf"  ,  "srv_mec" , "cld_host" , "cld_host_upf" , "srv_cld" ]
        colors  = [colors[1] ,  colors[2] ,  colors[2] ,  colors[2] ,  colors[3] , colors[3] , colors[3] ]
        markers = [      "." ,        "," ,        "." ,        "+" ,        "," ,       "." ,       "+" ]
        lw      = [       1  ,         2  ,         1  ,         1  ,         2  ,        1  ,        1  ]
    if idx == 2:
        c_names = [     "ran" , "mec_host" , "mec_host_upf"  ,  "srv_mec1" ,  "srv_mec2" , "cld_host" , "cld_host_upf" , "srv_cld" ]
        colors  = [colors[1] ,  colors[2] ,  colors[2] ,  colors[2]  ,  colors[2]  ,  colors[3] , colors[3] , colors[3] ]
        markers = [      "." ,        "," ,        "." ,        "+"  ,        "^"  ,        "," ,       "." ,       "+" ]
        lw      = [       1  ,         2  ,         1  ,         1   ,         1   ,         2  ,        1  ,        1  ]

    return c_names, colors, markers, lw

######################################################################################################
### Read/manipulate Results

def load_results_json( res_file ):
    with open( res_file, 'r') as f:
        return  json.load(f)

def load_results_dataframe( res_file ):
    with open( res_file, 'r') as f:
        results = json.load(f)
    create_dataframe( results )

def create_dataframe( results ):
    df = pd.DataFrame
    for cn in results["cpu"]:
        if cn=="sys" or cn=="ran": continue
        df_in = df_from_raw_samples( time=results["cpu"][cn]["time"], val=results["cpu"][cn]["cpu_perc"], col_name=f'cpu:{cn}' )
        df_in = resample_df_interpolating( df_in )
        df = df.join( df_in , how='outer' )
    for cn in results["traffic"]:
        for itf in results["traffic"][cn]:
            df_in = df_from_raw_samples( time=results["traffic"][cn]["ogstun_recv"]["time"], val=results["traffic"][cn]["ogstun_recv"]["val"], col_name=f'{cn}:{itf}' )
            df_in = resample_df_interpolating( df_in )
            df = df.join( df_in , how='outer' )

def df_from_raw_samples( time:list, val:list, col_name:str ):
    df = pd.DataFrame( { f"{col_name}":val} , index=pd.to_timedelta(time , unit='S') )
    return df

def resample_df_interpolating( df ):
    # take a df with multiple columns, rasample it (freq. = seconds) interpolating values
    t = pd.to_timedelta(np.arange( df.index[0].seconds+1 , df.index[-1].seconds+1 ),unit='S')
    union_idx = df.index.union(t)
    df = df.reindex(union_idx)
    df = df.interpolate(method='time', limit_direction='forward', axis=0 , limit_area='inside')
    df = df.loc[(df.index.microseconds==0)]
    return df


######################################################################################################
### PLOT RAW DATA

def plot_raw_cont_sys_cpu( res, ax  , bboxes=None, loc=None, scen_idx=1, colors=None ):
    
    c_names, colors, markers, lw = get_plot_info( scen_idx, colors )

    data = res["cpu"]
    ax.plot( data["sys"]["time"] , data["sys"]["cpu_perc"] , label="VM" , alpha=0.5, lw=3, linestyle='dashed'  )

    for i in range(len(c_names)):
        ax.plot( data[c_names[i]]["time"] , data[c_names[i]]["cpu_sys_perc"] , label=c_names[i] , color=colors[i] , marker=markers[i] , lw=lw[i])

    ax.set_ylabel('System CPU [%]')
    ax.legend( bbox_to_anchor=bboxes , loc=loc )
    ax.grid(visible=True)
    return ax

def plot_raw_cont_cpu( res, ax , bboxes=None, loc=None, scen_idx=1, colors=None  ):

    c_names, colors, markers, lw = get_plot_info( scen_idx, colors )

    data = res["cpu"]
    for i in range(len(c_names)):
        ax.plot( data[c_names[i]]["time"] , data[c_names[i]]["cpu_perc"] , label=c_names[i] , color=colors[i] , marker=markers[i] , lw=lw[i])

    ax.set_ylabel('Container CPU [%]')
    ax.legend( bbox_to_anchor=bboxes , loc=loc )
    ax.grid(visible=True)
    return ax

def plot_raw_upf_thr( res, ax , bboxes=None, loc=None, colors=None ):
    if colors is None:  colors = get_color_list()
    colors_it = itertools.cycle( colors )

    data = res["traffic"]
    for k in data.keys():
        for kk in data[k].keys():
            c = next(colors_it)
            ax.plot( data[k][kk]["time"] , data[k][kk]["val"] , label=f"{k}:{kk}", color=c )
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Mbps")    
    ax.legend( bbox_to_anchor=bboxes , loc=loc  )
    ax.grid(visible=True)
    return ax

def plot_raw_iperf_tcp_get_thrPerUeAllSessions( res, ue=0 ):
    iperf_dict = res["iperf"]
    thr=[]
    req=[]
    time=[]
    for session in iperf_dict:
        if session["ue_id"] != ue or  session["prot"]!="tcp":
            continue

        time.append( session["time"][0]-0.1 ) 
        time.extend( session["time"] )
        time.append( session["time"][-1]+0.1 )

        thr.append( 0 ) 
        thr.extend(  session["bwt"] )
        thr.append( 0 ) 

        req.append( 0 ) 
        req.extend( [session["mbps"]]*len( session["time"] ) )
        req.append( 0 ) 

    return time,thr,req

def plot_raw_iperf_tcp_mbps_PerUe( res, ax , ue="*", sess="*", colors=None , **kwargs):
    if colors is None:  colors = get_color_list()
    iperf_dict = res["iperf"]
    legend_added = False
    for session in iperf_dict:
        ue_id = session["ue_id"]
        if ue != "*"  and  ue_id != ue and  session["prot"]!="tcp":
            continue
        if sess != "*"  and  session["id"] != sess:
            continue
        if not legend_added:
            ax.plot(  session["time"], session["bwt"]                           , color=colors[ue_id] , label=f'UE {session["ue_id"]}'     ,  **kwargs)
            ax.plot(  session["time"], [session["mbps"]]*len( session["time"] ) , color=colors[ue_id] , label=f'Req. UE {session["ue_id"]}', alpha=0.5, lw=3 )
            legend_added = True
        else:
            ax.plot(  session["time"], session["bwt"]                           , color=colors[ue_id] , **kwargs )
            ax.plot(  session["time"], [session["mbps"]]*len( session["time"] ) , color=colors[ue_id] , alpha=0.5, lw=3 )

    ax.grid(visible=True)
    ax.set_xlabel("Time[s]")
    ax.set_ylabel("Mbps")
    ax.legend()

    return ax

def plot_raw_iperf_tcp_rtt_PerUe( res, ax , ue="*", sess="*", colors=None):
    if colors is None:  colors = get_color_list()
    iperf_dict = res["iperf"]
    legend_added = False
    for session in iperf_dict:
        ue_id = session["ue_id"]
        if ue != "*"  and  ue_id != ue and  session["prot"]!="tcp":
            continue
        if sess != "*"  and  session["id"] != sess:
            continue
        if not legend_added:
            ax.plot(  session["time"], session["rtt"] , color=colors[ue_id] , label=f'UE {session["ue_id"]}'     , alpha=1  , marker="." )
            legend_added = True
        else:
            ax.plot(  session["time"], session["rtt"] , color=colors[ue_id] , alpha=1  , marker="." )

    ax.grid(visible=True)
    ax.set_xlabel("Time[s]")
    ax.set_ylabel("RTT")
    ax.legend()
    return ax

def plot_raw_iperf_tcp_retx_PerUe( res, ax , ue="*", sess="*", colors=None):
    if colors is None:  colors = get_color_list()
    iperf_dict = res["iperf"]
    legend_added = False
    for session in iperf_dict:
        ue_id = session["ue_id"]
        if ue != "*"  and  ue_id != ue and  session["prot"]!="tcp":
            continue
        if sess != "*"  and  session["id"] != sess:
            continue
        if not legend_added:
            ax.plot(  session["time"], session["retx"] , color=colors[ue_id] , label=f'UE {session["ue_id"]}'     , alpha=1  , marker="." )
            legend_added = True
        else:
            ax.plot(  session["time"], session["retx"] , color=colors[ue_id] , alpha=1  , marker="." )
    ax.grid(visible=True)
    ax.set_xlabel("Time[s]")
    ax.set_ylabel("ReTX")
    ax.legend()
    return ax

def plot_raw_iperf_tcp_retx_comsum_PerUe( res, ax , ue="*", colors=None):
    if colors is None:  colors = get_color_list()
    iperf_dict = res["iperf"]
    legend_added = False
    for session in iperf_dict:
        ue_id = session["ue_id"]
        if ue != "*"  and  ue_id != ue and  session["prot"]!="tcp":
            continue
        if not legend_added:
            ax.plot(  session["time"], list(accumulate( session["retx"] )), color=colors[ue_id] , label=f'UE {session["ue_id"]}' , alpha=1  , marker="." )
            legend_added = True
        else:
            ax.plot(  session["time"], list(accumulate( session["retx"] )), color=colors[ue_id] , alpha=1  , marker="." )
    ax.grid(visible=True)
    ax.set_xlabel("Time[s]")
    ax.set_ylabel("ReTX")
    ax.legend()
    return ax

def plot_raw_iperf_tcp_PerUe( res, ax , ue="*", kpi="bwt",  colors=None):
    # kpi = ["bwt"|"rtt"|"retx"|"req"]
    if colors is None:  colors = get_color_list()
    iperf_dict = res["iperf"]
    legend_added = False
    for session in iperf_dict:
        ue_id = session["ue_id"]
        if ue != "*"  and  ue_id != ue and  session["prot"]!="tcp":
            continue
        if kpi =="req":
            y_data = [session["mbps"]]*len( session["time"] )
            marker=""
            lw=3
            alpha = 0.5
        else:
            y_data = session[kpi]
            marker="."
            lw=1
            alpha = 1
        if not legend_added:
            ax.plot(  session["time"], y_data , color=colors[ue_id] , marker=marker , label=f'UE {session["ue_id"]}' , lw=lw, alpha=alpha)
            legend_added = True
        else:
            ax.plot(  session["time"], y_data , color=colors[ue_id] , marker=marker  , lw=lw, alpha=alpha)
    ax.grid(visible=True)
    ax.set_xlabel("Time[s]")
    if kpi == "bwt" : ax.set_ylabel("Mbps")
    if kpi == "rtt" : ax.set_ylabel("RTT")
    if kpi == "retx": ax.set_ylabel("ReTX")
    ax.legend()
    return ax


######################################################################################################
######################################################################################################
######################################################################################################
######################################################################################################

def plot_iperf_rtt_avg( df, ax, legend, color="C0", alpha=0.3):
    ax.plot( df.index.total_seconds(), df["iperf_rtt_avg"].values , color=color , label=legend)
    ax.fill_between( df.index.total_seconds() , 
                        df["iperf_rtt_avg"].values - df["iperf_rtt_std"].values , 
                        df["iperf_rtt_avg"].values + df["iperf_rtt_std"].values , 
                        color=color,alpha=alpha)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("RTT")
    ax.grid(visible=True)
    ax.legend()
    return ax


def plot_iperf_retx_avg( df, ax, legend, color="C0",alpha=0.3):
    ax.plot( df.index.total_seconds(), df["iperf_retx_avg"].values , color=color , label=legend)
    ax.fill_between( df.index.total_seconds() , 
                        df["iperf_retx_avg"].values - df["iperf_retx_std"].values , 
                        df["iperf_retx_avg"].values + df["iperf_retx_std"].values , 
                        color=color,alpha=alpha)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Re-TX")
    ax.grid(visible=True)
    ax.legend()
    return ax

def plot_iperf_rx( res, ax , ue="*" , resampled=False, colors=None):
    if colors == None:
        prop_cycle = plt.rcParams['axes.prop_cycle']
        colors = prop_cycle.by_key()['color']
    
    if resampled:
        ue_list = list(set([ sub["ue_id"] for sub in res.results["iperf"]]))
        for ueid in ue_list:
            if ue != "*":
                if ueid != ue:
                    continue
            ax.plot(  res.df.index.total_seconds(), res.df[f"iperf_ue{ueid}_rx"] , color=colors[ueid] , marker="." , label=f"UE {ueid}")
    else:
        pass
        
    ax.grid(visible=True)
    ax.set_xlabel("Time[s]")
    ax.set_ylabel("Mbps")
    ax.legend()
    return ax


def plot_iperf_rx_avg( res, ax, label, color="C0", alpha=0.3):
    ax.plot( res.df.index.total_seconds(), res.df["iperf_rx_avg"].values , color=color , label=label)
    ax.fill_between( res.df.index.total_seconds() , 
                        res.df["iperf_rx_avg"].values - res.df["iperf_rx_std"].values , 
                        res.df["iperf_rx_avg"].values + res.df["iperf_rx_std"].values , 
                        color=color,alpha=alpha)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Mbps")
    ax.grid(visible=True)
    ax.legend()
    return ax


def plot_iperf_retx( res, ax , ue="*"):
    prop_cycle = plt.rcParams['axes.prop_cycle']
    colors = prop_cycle.by_key()['color']

    col_list = [s for s in  list(res.df.columns) if ("iperf:ue" in s) and (f":retx" in s) ]
    cnt = 0
    for col in col_list:
        ueid = col.replace("iperf:ue","")
        ueid = ueid.replace(":retx","")
        if ue != "*":
            if ueid != ue:
                continue
        ax.plot(  res.df.index.total_seconds() , res.df[col] ,  color=colors[cnt] , marker="." , label=f"UE{ueid}" )
        cnt += 1

    ax.grid(visible=True)
    ax.set_xlabel("Time[s]")
    ax.set_ylabel("ReTX")
    ax.legend()
    return ax


######################################################################################################
### SCATTER PLOTs

def plot_scatter( df, ax, x_column, y_column, xlabel, ylabel, alpha=0.5, **kwargs):
    ax.scatter( df[x_column], df[y_column],  alpha=alpha, **kwargs)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    ax.set_box_aspect(1)
    ax.grid(visible=True)
    return ax

def plot_scatter_fit( df, ax, x_column, y_column, xlabel, ylabel, x_lim=None, polyorder=2,  color="C0" , alpha=0.5, **kwargs):
    x_line, y_line = fitting_scatter_plot( df, x_column, y_column, x_lim , polyorder)

    ax.plot(x_line, y_line, '--', color=color , **kwargs)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    ax.set_box_aspect(1)
    ax.grid(visible=True)
    return ax

def plot_scatter_and_fit( df, ax, x_column, y_column, xlabel, ylabel, x_lim=None, polyorder=2,  color="C0" , alpha=0.5, **kwargs):
    ax.scatter( df[x_column], df[y_column],  color=color, alpha=0.5, **kwargs)
    plot_scatter_fit( df, ax, x_column, y_column, xlabel, ylabel, x_lim=x_lim, polyorder=2,  color=color , alpha=alpha, **kwargs)
    return ax


def plot_scatter_udp( df, ax, label, color="C0"):

    def objective(x, a, b, c):
        return a * x + b * x**2 + c

    ax[0].scatter( df["mec_host:ogstun_recv"], df["cpu:mec_host"],  color=color, label=label,  alpha=0.5)
    ax[0].set_xlabel("THR")
    ax[0].set_ylabel("CPU")
    ax[0].legend()
    ax[0].set_box_aspect(1)
    ax[0].grid(visible=True)

    x = df["mec_host:ogstun_recv"].values
    y = df["cpu:mec_host"].values
    popt, _ = curve_fit(objective, x , y )
    a, b, c = popt
    x_line = arange(min(x), max(x), 1)
    y_line = objective(x_line, a, b, c)
    ax[0].plot(x_line, y_line, '--', color=color)

    ax[1].scatter( df["mec_host:ogstun_recv"], df[f"iperf_latency_avg"], color=color, label=label, alpha=0.5)
    ax[1].set_xlabel("THR")
    # ax[1].scatter( df[f"cpu:upf_mec"], df["iperf_latency_avg"], color=color, label=label, alpha=0.5)
    # ax[1].set_xlabel("CPU")
    ax[1].set_ylabel("Delay")
    ax[1].legend()
    ax[1].set_box_aspect(1)
    ax[1].grid(visible=True)

    ax[2].scatter( df["mec_host:ogstun_recv"], df[f"iperf_pktloss_avg"], color=color, label=label,  alpha=0.5)
    ax[2].set_xlabel("THR")
    # ax[2].scatter( df["cpu:upf_mec"], df[f"iperf_pktloss_avg"], color=color, label=label,  alpha=0.5)
    # ax[2].set_xlabel("CPU")
    ax[2].set_ylabel("Packet Loss %")
    ax[2].legend()
    ax[2].set_box_aspect(1)
    ax[2].grid(visible=True)

    return ax

######################################################################################################
### PLOT PDF AND CDF

def plot_pdf(df, col_name, x_lab, y_lab, ax, label, color="C0" ):
    df[col_name].plot.density( ax=ax, label=label, color=color )
    ax.legend()
    ax.grid(visible=True)
    ax.set_xlabel(x_lab)
    ax.set_ylabel(y_lab)

def plot_cdf(df, col_name, x_lab, y_lab, ax, label, color="C0" ):
    count1, bins_count1 = np.histogram(df[col_name].dropna().values, bins=1000)
    pdf1 = count1 / sum(count1)
    cdf1 = np.cumsum(pdf1)
    ax.plot(bins_count1[1:], cdf1, label=label)
    ax.legend()
    ax.grid(visible=True)
    ax.set_xlabel(x_lab)
    ax.set_ylabel(y_lab)


