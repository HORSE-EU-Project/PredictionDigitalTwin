#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import docker, psutil, time
import dateutil.parser
import numpy as np
from threading import Condition, Thread, Event


class CPUMonitorThread(Thread):
    """
       Monitors the CPU status of the containers
    """

    def __init__(self, c_name, container=None):
        
        self.shutdown_flag = Event()

        if c_name == "sys":
            self.c_name = c_name
            list_kpi = ["time", "cpu_perc"]

        else: 
            self.c_name = c_name
            self.container = container

            self.api_client = docker.APIClient(base_url='unix:///var/run/docker.sock')
            self.stats_obj = self.api_client.stats(c_name , decode=True, stream=True)

            list_kpi = ["time",
                        "time_delta",
                        "cpu_sys_perc",
                        "cpu_period",
                        "cpu_quota",
                        "cpu_delta",
                        "cpu_throttle_delta",
                        "mem_rss",
                        "cpu_perc"]

        self.results = dict()
        for k in list_kpi:
            self.results[k] = []
        
        super(CPUMonitorThread, self).__init__()
        self.paused = True  # Start out paused.
        self.state = Condition()


    def pause(self):
        with self.state:
            self.paused = True  # Block self.

    def resume(self):
        with self.state:
            self.paused = False
            self.state.notify()  # Unblock self if waiting.

    def stop(self):
        self.shutdown_flag.set()

    def get_container_cpu_usage( self ):
        return self.results["cpu_perc"]

    def get_last_cpu_usage( self  ):
        if len(self.results["time_delta"]) == 0:
            return 0
        return self.results["cpu_perc"][-1]

    def run(self):
        self.shutdown_flag.clear()
        self.resume()

        while not self.shutdown_flag.is_set():
            with self.state:
                if self.paused:
                    self.state.wait()  # Block execution until notified.
            
            if self.c_name == "sys":
                sample_time = time.time()
                self.results["time"].append( sample_time  )
                self.results["cpu_perc"].append( psutil.cpu_percent() )
                time.sleep(1)
                continue

            stat = next(self.stats_obj) # Get next measure for container

            sample_time = time.time()
            t_read    = dateutil.parser.isoparse( stat["read"] )
            t_preread = dateutil.parser.isoparse( stat["preread"] )
            diff = t_read - t_preread
            timeDelta = diff.seconds*1e6 + diff.microseconds

            cpupercentage = 0.0

            prestats = stat['precpu_stats']
            cpustats = stat['cpu_stats']

            prestats_totalusage = prestats['cpu_usage']['total_usage']
            stats_totalusage = cpustats['cpu_usage']['total_usage']
            # numOfCPUCore = len(cpustats['cpu_usage']['percpu_usage'])

            if 'system_cpu_usage' in prestats:
                prestats_syscpu = prestats['system_cpu_usage']
            else:
                continue
            stats_syscpu = cpustats['system_cpu_usage']

            cpuDelta = stats_totalusage - prestats_totalusage
            systemDelta = stats_syscpu - prestats_syscpu

            if cpuDelta > 0 and systemDelta > 0:
                # cpupercentage = (cpuDelta / systemDelta) * numOfCPUCore * 100
                cpupercentage = (cpuDelta / systemDelta) * 100

            CpuPeriod = self.container.attrs["HostConfig"]["CpuPeriod"]
            CpuQuota  = self.container.attrs["HostConfig"]["CpuQuota"]

            cpuDelta_micro_sec = cpuDelta / 1e3
            cpu_throttle_delta = (cpustats["throttling_data"]["throttled_time"] - prestats["throttling_data"]["throttled_time"]) / 1e3

            if CpuPeriod <= 0 or CpuQuota <= 0:
                cpu_delta_max = timeDelta
            else:
                cpu_delta_max = (CpuQuota/CpuPeriod) * timeDelta
            cont_cpu_perc = 100 * cpuDelta_micro_sec / cpu_delta_max

            self.results["time"].append( sample_time )
            self.results["cpu_sys_perc"].append( cpupercentage )
            self.results["time_delta"].append( timeDelta )
            self.results["cpu_delta"].append( cpuDelta_micro_sec )
            self.results["cpu_period"].append( CpuPeriod )
            self.results["cpu_quota"].append( CpuQuota )
            self.results["cpu_throttle_delta"].append( cpu_throttle_delta )
            self.results["cpu_perc"].append( cont_cpu_perc )
