#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import docker, redis, time
from docker.models.containers import Container
from python_modules.CPUMonitorThread import CPUMonitorThread

class MonitorScenario:
    def __init__( self ):
        self.d_client = docker.from_env()

        redis_ip = self.d_client.containers.get("my-redis").attrs['NetworkSettings']['IPAddress']
        self.redis_cli = redis.StrictRedis(host=redis_ip, port=6379, password="", decode_responses=True)

        self.start_time        = 0
        self.is_start_time_set = False

        self.cpu_monitors = dict()

    ##############################################################################

    def set_start_time( self  ):
        if not self.is_start_time_set:
            self.start_time = time.time()
            self.is_start_time_set = True

    def start_cpu_monitor( self , c_name):
        if c_name == "sys":
            cpu_mon = CPUMonitorThread( c_name  )
        else:
            cpu_mon = CPUMonitorThread( c_name, self.get_container(c_name) )
        self.cpu_monitors[c_name] = cpu_mon
        cpu_mon.start()

    def stop_cpu_monitor( self , c_name):
        self.cpu_monitors[c_name].stop()
        self.cpu_monitors[c_name].join()

    def start_all_monitors( self ):
        self.set_start_time()
        self.start_cpu_monitor( "sys" )
        for c in self. d_client.containers.list():
            self.start_cpu_monitor( c.name )
        self.redis_cli.publish('throughput_monitoring', "start" )

    def stop_all_monitors(self):
        for k in self.cpu_monitors:
            self.stop_cpu_monitor(k)
        self.redis_cli.publish('throughput_monitoring', "stop" )

    def get_redis_cli(self):
        return self.redis_cli
        
    def clean_redis(self):
        for key in self.redis_cli.scan_iter("*"):
            self.redis_cli.delete(key)

    def get_container( self, c_name:str  ) -> Container:
        return self.d_client.containers.get(c_name)

    def update_host_resources( self, h_name:str, sys_cpu_perc:float ):
        # sys_cpu_perc = [0:1]
        if h_name not in self.host_struct:
            print(f'Error: Update called for host "{h_name}" but it is not in the list of availavle hosts: {self.host_struct.keys() }.')
            return
        cpu_period_new = 100000
        cpu_quota_new  = int( cpu_period_new*sys_cpu_perc )
        
        self._update_container( h_name, cpu_period_in=cpu_period_new , cpu_quota_in=cpu_quota_new )
        
        # NOTE: Do not update the child containers: let it adapt to the DockerHost CPU constraints
        # childs = list( self.host_struct[h_name].values() )
        # for cn in childs:
        #     if type(cn) is list:
        #         for tmp in cn:
        #             self._update_container( tmp, cpu_period_in=cpu_period_new , cpu_quota_in=cpu_quota_new )
        #     else:
        #         self._update_container( cn, cpu_period_in=cpu_period_new , cpu_quota_in=cpu_quota_new )


    def _update_container( self, c_name:str , cpu_period_in:int , cpu_quota_in:int  ):
        self.containers[c_name].update( cpu_period=cpu_period_in , cpu_quota=cpu_quota_in )
        self.containers[c_name] = self.get_container( c_name )
        return self.containers[c_name]

    def is_process_running ( self, c_name:str, process_tag:str):
        top = self.d_client.containers.get( c_name ).top()

        p_names = [p[-1] for p in top['Processes']]
        for p in p_names:
            if process_tag in p:
                return True
        return False

    ### Handle containers' CPU load generation
    def set_cpu_load( self, c_name:str, load:float ):
        # Load = [0:1]
        self.redis_cli.publish(f'{c_name}_cpu_load', str(load) )

    def start_cpu_stress( self, c_name:str ):
        if not self.is_process_running( c_name, "cpu_load_gen.py" ):
            self.get_container( c_name ).exec_run( cmd=f'python3 /mnt/volume_util/cpu_load_gen.py' , detach=True )

        self.redis_cli.publish(f'{c_name}_cpu_stress' , "start" )

    def stop_cpu_stress( self, c_name:str ):
        self.redis_cli.publish(f'{c_name}_cpu_stress' , "stop" )

    def start_passmark_test( self, c_name:str ):
        self.get_container( c_name ).exec_run( cmd="/bin/bash /mnt/volume_util/PassMark/run.sh" , tty=True , detach=True )

    def stop_passmark_test( self, c_name:str ):
        self.get_container( c_name ).exec_run( cmd="python3 /mnt/volume_util/pskill.py pt_linux_x64" , detach=False )

    def start_cpu_follow_thr( self ):
        self.redis_cli.publish('start_cpu_follow_throughput' , str(0.0) )

    def stop_cpu_follow_thr( self ):
        self.redis_cli.publish('stop_cpu_follow_throughput' , str(0.0) )


    ### Retrieve results
    def get_container_cpu_usage( self, c_name:str ):    
        return self.cpu_monitors[c_name].get_container_cpu_usage(c_name)

    def get_last_cpu_usage( self, c_name:str ):    
        return self.cpu_monitors[c_name].get_last_cpu_usage(c_name)

    # Return all the stored results for the CPU in a dictionary format
    def get_cpu_results( self ):
        results = dict()
        for k in self.cpu_monitors:
            results[k] = self.cpu_monitors[k].results
            results[k]["time"] = [ x-self.start_time  for x in results[k]["time"] ]
        return results
