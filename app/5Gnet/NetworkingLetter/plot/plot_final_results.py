#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import time, sys, os, json, copy, itertools, pathlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import ScalarFormatter, FormatStrFormatter
from scipy import interpolate
from scipy.interpolate import UnivariateSpline, CubicSpline, InterpolatedUnivariateSpline

sys.path.append('c:\\Users\\rfedrizzi\\GitHub_repos\\comnetsemu\\app\\5Gnet')
sys.path.append('c:\\Users\\rfedrizzi\\GitHub_repos\\comnetsemu\\app\\5Gnet\\python_modules')
from PlotResults.LoadResults import LoadResults
import PlotResults.plot_res as p

colors_it = itertools.cycle( ["C0","C1","C2","C3"] )

def main(argv):

    if len(argv) > 1:
        which_plot = argv[1]
    else:
        fig_1a()
        # fig_1b()    
        # fig_scenario1()
        # scenario2_fig1()
        # scenario2_fig2()
        # PlotPassMark()

    if which_plot=="fig_1a":           fig_1a("fig_1a.pdf")
    if which_plot=="fig_1b":           fig_1b("fig_1b.pdf")
    if which_plot=="fig_scenario1":    fig_scenario1("fig_scenario1.pdf")
    if which_plot=="fig_scenario2_1":  fig_scenario2_1("fig_scenario2_1.pdf")
    if which_plot=="fig_scenario2_2":  fig_scenario2_2("fig_scenario2_2.pdf")

    os.system( f'pdfcrop {which_plot}.pdf {which_plot}.pdf' )

########################################################################################################
########################################################################################################
def fig_1a(filename):

    f = open( "../FinalResults/Res_CPU_benchmark.json" )
    results = json.load(f)
    f.close()

    rasPiRes = [439.1]

    keys = list( results.keys() )
    keys.sort( key=int )
    xTicks = 100*np.array([int(x) for x in keys])/100000

    res_x = []
    res_y = []
    for key in keys[3::]:
        for i in range( len(results[key]) ):
            res_x.append( int(key) * 100 / 100000 )
            res_y.append( results[key][i]["Results"]["SUMM_CPU"] )

    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(6, 6))

    ax.axhline( rasPiRes            , linestyle=':'  , c='C1', lw=3, label="RasPi Model 3" )
    ax.axhline( np.array(rasPiRes)*2, linestyle='--' , c='C2', lw=3, label="2 x RasPi Model 3" )
    ax.axhline( np.array(rasPiRes)*3, linestyle='-.' , c='C3', lw=3, label="3 x RasPi Model 3" )

    spl = UnivariateSpline(res_x, res_y, k=3, s=100000)
    xs = np.linspace(1, 100, 50)
    ax.plot(xs, spl(xs), 'C0', lw=3, label="DockerHost")

    ax.scatter(res_x,res_y, alpha=0.5 )

    ax.grid()
    ax.set_ylabel("CPU Mark")
    ax.set_xlabel("Allocated CPU %")
    ax.set_ylim([0, 1800])
    # ax.set_xscale('log')
    # ax.xaxis.set_tick_params(which='minor')
    # # ax.xaxis.set_minor_formatter(FormatStrFormatter("%.0f"))
    # ax.xaxis.set_minor_formatter(ScalarFormatter())
    # ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.legend(bbox_to_anchor=(0.04, 0.72, 1., .102), fontsize=18, labelspacing=0.1)
    # ax1.legend( bbox_to_anchor=(0.04, 0.82, 1., .102),
    #             labelspacing=0.1,       handlelength=0.1, handletextpad=0.1,frameon=False, ncol=4, columnspacing=0.7)

    ax.xaxis.label.set_fontsize(20)
    ax.yaxis.label.set_fontsize(20)
    ax.tick_params(axis='x', labelsize=20 )
    ax.tick_params(axis='y', labelsize=20 )

    plt.tight_layout()
    plt.savefig( filename )
    plt.show()

########################################################################################################
########################################################################################################
def fig_1b( filename ):
    fig, ax = plt.subplots(nrows=2, ncols=1, sharex=True , figsize=(12,6) )

    file = '../FinalResults/Test_scenario0_iperf_cubic_cpu0.375.json'

    res = p.load_results_json( file )
    time,thr,req = p.plot_raw_iperf_tcp_get_thrPerUeAllSessions( res, ue=0)

    ax[0].plot( res["cpu"]["sys"]["time"] , res["cpu"]["sys"]["cpu_perc"] , label="System CPU Usage" , alpha=0.5, lw=3  )
    ax[0].plot( res["cpu"]["mec_host"]["time"] , res["cpu"]["mec_host"]["cpu_perc"] , label="MEC Host CPU Usage" , color="C2" , marker="" , lw=2)
    # ax[0][0].plot( res["cpu"]["ue"]["time"] , res["cpu"]["ue"]["cpu_perc"] , label="UE" , color="C1" , marker="" , lw=1)
    # p.plot_raw_iperf_tcp_mbps_PerUe( res, ax[1][0] , ue="*", colors=p.get_color_list() )
    ax[1].plot(  time , req , color="C1" , label=f'Expected Throughput', alpha=0.5, lw=3 )
    ax[1].plot(  time , thr , color="C0" , label=f'UE Throughput'    , lw=2 )

    x=[31,51]
    ax[0].fill_between( [x[0],x[1]] , [0,0] , [150,150] , color="C0" , alpha=0.2 )
    x=[51,71]
    ax[0].fill_between( [x[0],x[1]] , [0,0] , [150,150] , color="C1" , alpha=0.2 )

    x=[80.5,184.5]
    ax[0].fill_between( [x[0],x[1]] , [0,0] , [150,150] , color="C0" , alpha=0.2 )
    ax[1].fill_between( [x[0],x[1]] , [0,0] , [150,150] , color="C0" , alpha=0.2 )

    x=[194.5,299]
    ax[0].fill_between( [x[0],x[1]] , [0,0] , [150,150] , color="C1" , alpha=0.2 )
    ax[1].fill_between( [x[0],x[1]] , [0,0] , [150,150] , color="C1" , alpha=0.2 )

    ax[0].text( 10, 20, "(1)", size=18, rotation=0, ha="center", va="center", style='normal')
    ax[0].text( 20, 35, "(2)", size=18, rotation=0, ha="center", va="center", style='normal')
    ax[0].text( 41   , 93, "(3)", size=18, rotation=0, ha="center", va="center", style='normal')
    ax[0].text( 61   , 93, "(4)", size=18, rotation=0, ha="center", va="center", style='normal')
    ax[0].text( 132.5, 93, "(5)", size=18, rotation=0, ha="center", va="center", style='normal')
    ax[0].text( 210, #246.5, 
                93, "(6)", size=18, rotation=0, ha="center", va="center", style='normal')

    # bbox_to_anchor=(x0, y0, width, height)
    ax[0].legend( bbox_to_anchor=(0.62, 0.43), fontsize=20, labelspacing=0.1, handlelength=1, handletextpad=0.1)
    ax[1].legend( bbox_to_anchor=(0.36, 0.55), fontsize=20, labelspacing=0.1, handlelength=1, handletextpad=0.1)
    ax[0].set_ylabel( "CPU Usage [%]" , fontsize=20)
    ax[1].set_ylabel( "Throughput [Mpbs]" , fontsize=20)
    ax[1].set_xlabel( "Time [s]" , fontsize=20)
    ax[0].grid(visible=True)
    ax[1].grid(visible=True)
    ax[0].set_ylim(0,100)
    ax[1].set_ylim(0,90)
    ax[0].set_xlim(0,310)
    ax[1].tick_params(axis='x', labelsize=20 )
    ax[0].tick_params(axis='y', labelsize=20 )
    ax[1].tick_params(axis='y', labelsize=20 )

    plt.tight_layout()
    plt.savefig( filename )
    plt.show()

########################################################################################################
########################################################################################################
def fig_scenario1( filename ):
    # SCATTER PLOT - MEC CPU vs. Throughput
    # xMax = [None,None,None,None]
    # xMax = [None,None,65,40]
    xMax = [None,75,60,35]

    fig1, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(6,6) )

    for hcpu in [ 1, 0.7, 0.375, 0.2]:
        c = next(colors_it)
        
        ##### SCENARIO 1a
        # res = LoadResults( f'results/PerfHOST_tcp_mec_hostcpu{hcpu}_nue1_sliceFalse_continuousTX.json', load=True )
        
        ##### SCENARIO 1b
        res = LoadResults( f'../FinalResults/Res_scen1b_tcp_cubic_hostcpu{hcpu}.json', load=True )
        
        df_sum, _ = res.df_iperf_bwt( )
        res.df = res.df.join(df_sum, how="outer")
        p.plot_scatter(     res.df, ax1, "cpu:mec_host","iperf:ue0:bwt:sum", "", "", label=f"MEC CPU {hcpu*100}%" , color=c)
        p.plot_scatter_fit( res.df, ax1, "cpu:mec_host","iperf:ue0:bwt:sum", "", "", color=c)

    ax1.set_xlim(0,110)
    ax1.set_ylim(5,90)
    ax1.legend( bbox_to_anchor=(0.05, 0.92, .97, .10), fontsize=18 , loc='upper right', ncol=2 ,
                 labelspacing=0.1, handlelength=1, handletextpad=0.1, columnspacing=0.2)
    # ax1.legend( bbox_to_anchor=(0.04, 0.82, 1., .102),
    #             labelspacing=0.1,       handlelength=0.1, handletextpad=0.1,frameon=False, ncol=4, columnspacing=0.7)

    ax1.grid(visible=True)
    ax1.set_xlabel("MEC CPU Load %", fontsize=20)
    ax1.set_ylabel("MEC Throughput [Mbps]", fontsize=20)
    ax1.set_box_aspect(1)
    ax1.tick_params(axis='x', labelsize=20 )
    ax1.tick_params(axis='y', labelsize=20 )
    
    plt.tight_layout()
    plt.savefig( filename )
    plt.show()

########################################################################################################
########################################################################################################
def fig_scenario2_1(filename):

    colors_it = itertools.cycle( ["C0","C1","C2","C3"] )

    fig1, ax1   = plt.subplots( nrows=1, ncols=1, figsize=(6,6) )
    final_x = []
    final_y = []

    hcpu = [1, 0.7, 0.375, 0.2]
    for i in [0,1,2,3]:
        c = next(colors_it)

        res = LoadResults( f'../FinalResults/Res_scen2_tcp_cubic_hostcpu{hcpu[i]}.json' , load=True )
        df_sum, _ = res.df_iperf_bwt()
        res.df = res.df.join( df_sum, how="outer" )
        df = res.df

        col = 'iperf:ue0:bwt:sum'
        roll = df[col].rolling( 10 , center=True ).mean()
        df[col+'_roll'] = roll
        col = 'mec_host:ogstun_recv'
        roll = df[col].rolling( 5, center=True ).mean()
        df[col+'_roll'] = roll
        col = 'cpu:srv_mec2'
        roll = df[col].rolling( 5 , center=True ).mean()
        df[col+'_roll'] = roll

        # p.plot_scatter( df, ax1, 'cpu:srv_mec2', "iperf:ue0:bwt:sum", "srv_mec2: MEC CPU usage %", "Throughput [Mbps]",label=f"MEC CPU {hcpu[i]*100}%", color=c, alpha=0.2)
        # p.plot_scatter( df, ax1, 'cpu:srv_mec2', "iperf:ue0:bwt:sum_roll", "srv_mec2: MEC CPU usage %", "Throughput [Mbps]", color=c, alpha=0.2)
        # p.plot_scatter( df, ax1, 'cpu:srv_mec2', "iperf:ue0:bwt:sum_roll", "srv_mec2: MEC CPU usage %", "Throughput [Mbps]",label=f"MEC CPU {hcpus[i]*100}%",color=c, alpha=0.2)
        ax1.scatter( df['cpu:srv_mec2'], df["iperf:ue0:bwt:sum"], color=c, alpha=0.2)

        ### ADD average and std by splitting the srv_mec2 in bins
        # thr_col = 'iperf:ue0:bwt:sum_roll'
        thr_col = 'iperf:ue0:bwt:sum'
        # thr_col = 'mec_host:ogstun_recv_roll'
        # thr_col = 'mec_host:ogstun_recv'

        # cpu_col = 'cpu:srv_mec2_roll'
        cpu_col = 'cpu:srv_mec2'
        dftmp = df[[ cpu_col,thr_col ]]

        # bins = pd.cut(df[cpu_col], bins=10) # , labels=("1", "2", "3"))
        # bins_int = [0,10,20,30,40,50,60,70,80,90,100]
        bins_int = [-5,5,15,25,35,45,55,65,75,85,95]
        bins = pd.cut(dftmp[cpu_col], bins_int)
        dftmp = dftmp.groupby(bins).agg(["mean", "std"])
        dftmp["x_val"] = [x+5 for x in bins_int[0 : dftmp.shape[0] ]]

        # display(dftmp)
        dftmp = dftmp.dropna()
        x = dftmp["x_val"]
        y = dftmp[thr_col]["mean"]

        final_x.append( list(x) )
        final_y.append( list(y) )

    final_x_c = copy.deepcopy(final_x)
    final_y_c = copy.deepcopy(final_y)
    final_x_c[0].append(90)
    final_y_c[0].append(final_y[0][-1])
    final_x_c.append(final_x_c[0])
    final_y_c.append([0]*len(final_x_c[0]))

    for i in [0,1,2,3]:
        ax1.plot( final_x_c[i] , final_y_c[i] , label=f"MEC CPU {hcpu[i]*100}%")
        ax1.fill_between(final_x_c[i], final_y_c[i], final_y_c[i+1]  , alpha = 0.2)

    ax1.grid(visible=True)
    ax1.set_xlim(0,90)
    ax1.set_ylim(bottom=0,top=50)
    ax1.set_xlabel("APP 2: MEC CPU usage %", fontsize=20)
    ax1.set_ylabel("APP 1: Throughput [Mbps]", fontsize=20)
    # ax1.legend( fontsize=20 )
    ax1.legend( bbox_to_anchor=(0.55, 0.3), fontsize=18 , ncol=1 ,
                 labelspacing=0.1, handlelength=0.9, handletextpad=0.1, columnspacing=0.2)

    ax1.set_box_aspect(1)
    ax1.tick_params(axis='x', labelsize=20 )
    ax1.tick_params(axis='y', labelsize=20 )

    plt.tight_layout()
    plt.savefig( filename )
    plt.show()

########################################################################################################
########################################################################################################
def fig_scenario2_2( filename ):
    colors_it = itertools.cycle( ["C0","C1","C2","C3"] )
    fig, ax   = plt.subplots(nrows=1, ncols=1, figsize=(6,6) )

    hcpu = [1, 0.7, 0.375, 0.2]
    
    for i in [0,1,2,3]:
        c = next(colors_it)
        res = LoadResults( f'../FinalResults/Res_scen2_tcp_cubic_hostcpu{hcpu[i]}.json', load=True )
        df_sum, _ = res.df_iperf_bwt()
        res.df = res.df.join( df_sum, how="outer" )
        df = res.df

        col = 'cpu:mec_host'
        roll = df[col].rolling( 5 , center=True ).mean()
        df[col+'_roll'] = roll
        
        col = 'cpu:srv_mec2'
        roll = df[col].rolling( 5 , center=True ).mean()
        df[col+'_roll'] = roll
        
        col = 'mec_host:ogstun_recv'
        roll = df[col].rolling( 5 , center=True ).mean()
        df[col+'_roll'] = roll

        col = 'iperf:ue0:bwt:sum'
        roll = df[col].rolling( 5 , center=True ).mean()
        df[col+'_roll'] = roll

        # thr_col = 'iperf:ue0:bwt:sum_roll'
        thr_col = 'iperf:ue0:bwt:sum'
        # thr_col = 'mec_host:ogstun_recv_roll'
        # thr_col = 'mec_host:ogstun_recv'
        # p.plot_scatter( df, ax[0], "cpu:srv_mec2"     , thr_col        ,"srv_mec2: MEC CPU usage %", "srv_mec1: MEC Throughput [Mbps]", label=f"MEC CPU {hcpu*100}%" , color=c)
        # p.plot_scatter( df, ax[0], "cpu:mec_host"     , "cpu:srv_mec2" , "MEC host CPU load"       ,"srv_mec2: MEC CPU usage %", label=f"MEC CPU {hcpu[i]*100}%" , color=c)

        # ax[0].scatter( df['cpu:mec_host'] , df['cpu:srv_mec2']                   , label=f"MEC CPU {hcpu[i]*100}%" , color=c, alpha=0.3)
        ax.scatter( df["cpu:srv_mec2"] , df["cpu:srv_mec1"]+df["cpu:upf_mec"] , label=f"MEC CPU {hcpu[i]*100}%" , color=c, alpha=0.3 )

    ax.fill_between([0,100],[100,0],[100,100], alpha=0.2)
    ax.text( 55, 55, "Unfeasible region", size=20, rotation=-45,
         ha="center", va="center", style='normal'
        #  bbox=dict(boxstyle="round",
        #            ec=(1., 0.5, 0.5),
        #            fc=(1., 0.8, 0.8),
        #            )
         )

    ax.grid( visible=True )
    ax.set_box_aspect(1)
    ax.set_ylim( 0,100 )
    ax.set_xlim( 0,100 )
    ax.set_xlabel( "MEC CPU Usage for APP2" , fontsize=20 )
    ax.set_ylabel( "MEC CPU Usage for UPF and APP1" , fontsize=20 )
    ax.legend( bbox_to_anchor=(0.42, 0.69), fontsize=18 , ncol=1 ,
                 labelspacing=0.1, handlelength=0.9, handletextpad=0.1, columnspacing=0.2)

    ax.tick_params( axis='x', labelsize=20 )
    ax.tick_params( axis='y', labelsize=20 )

    plt.tight_layout()
    plt.savefig( filename )
    plt.show()



########################################################################################################
########################################################################################################
def PlotPassMark():

    f = open( "../FinalResults/Res_CPU_benchmark.json" )
    results = json.load(f)
    f.close()

    res = dict()
    res["SUMM_CPU"] = []
    res["CPU_FLOATINGPOINT_MATH"] = []
    res["CPU_INTEGER_MATH"] = []

    # RasPi results (one-shot measure from RasPi):
    #   CPU_INTEGER_MATH: 2330.6223333333332
    #   CPU_FLOATINGPOINT_MATH: 1216.9315950256928
    #   SUMM_CPU: 439.1035882207413
    rasPiRes = [439.1, 1216, 2330]
    ylabels = ["CPU Mark", "FLOATINGPOINT_MATH [MOps/Sec]", "INTEGER_MATH [MOps/Sec]"]
    ylim_max = [2000, 5000, 5000]    
    plot_cat = list( res.keys() )

    keys = list( results.keys() )
    keys.sort( key=int )
    xTicks = 100*np.array([int(x) for x in keys])/100000

    for key in keys:
        res["SUMM_CPU"].append(               np.array( [results[key][i]["Results"]["SUMM_CPU"] for i in range(len(results[key]))] ) )
        res["CPU_FLOATINGPOINT_MATH"].append( np.array( [results[key][i]["Results"]["CPU_FLOATINGPOINT_MATH"] for i in range(len(results[key]))] ) )
        res["CPU_INTEGER_MATH"].append(       np.array( [results[key][i]["Results"]["CPU_INTEGER_MATH"] for i in range(len(results[key]))] ) )

    fig, axs = plt.subplots(nrows=1, ncols=3, figsize=(17, 5))

    for i in range( len( ylabels ) ):
        axs[i].boxplot(res[ plot_cat[i] ])
        axs[i].axhline(rasPiRes[i], c='r', label="RasPi Model 3" )
        axs[i].set_xticklabels( xTicks ) #, rotation=45, fontsize=8)
        axs[i].grid()
        axs[i].set_ylabel(ylabels[i])
        axs[i].set_xlabel("Allocated CPU %")
        axs[i].set_ylim([0, ylim_max[i]])
        axs[i].legend()

    plt.show()

##########################################
if __name__ == "__main__":
    # print( 'Number of arguments:', len(sys.argv), 'arguments.' )
    # print( 'Argument List:', str(sys.argv) )
    main( sys.argv )

