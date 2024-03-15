#!/usr/bin/env python3

import os, sys, psutil, redis, time, docker

from threading import Condition, Thread, Event, RLock

class MonitorThread(Thread):
    """
       Monitors the CPU status
    """

    def __init__(self, cpu_core, interval):
        # synchronization
        self.shutdown_flag = Event()
        self.sleep_lock = RLock()
        self.cpu_lock = RLock()

        self.sampling_interval = interval  # sample time interval
        self.sample = 0.5  # cpu load measurement sample
        self.cpu = 0.5  # cpu load filtered

        self.alpha = 1  # filter coefficient
        self.sleepTimeTarget = 0.03
        self.sleepTime = 0.03
        self.cpuTarget = 0.5
        self.cpu_core = cpu_core
        self.dynamics = {"time"     : [], "cpu": [], "sleepTimeTarget": [],
                         "cpuTarget": [], "sleepTime": [], }
        super(MonitorThread, self).__init__()
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

    def get_cpu_load(self):
        with self.cpu_lock:
            return self.cpu

    def set_cpu_load(self, load):
        with self.cpu_lock:
            self.cpu = load

    def set_sleep_time_target(self, sleep_time_target):
        self.sleepTimeTarget = sleep_time_target

    def set_sleep_time(self, sleep_time):
        with self.sleep_lock:
            self.sleepTime = sleep_time

    def set_cpu_target(self, cpu_target):
        self.cpuTarget = cpu_target

    def get_dynamics(self):
        return self.dynamics

    def run(self):
        start_time = time.time()
        p = psutil.Process(os.getpid())

        self.shutdown_flag.clear()
        self.resume()
        while not self.shutdown_flag.is_set():
            with self.state:
                if self.paused:
                    self.state.wait()  # Block execution until notified.
            
            self.sample = p.cpu_percent(self.sampling_interval)
            # self.sample = psutil.cpu_percent(self.sampling_interval)

            # first order filter on the measurement samples
            self.set_cpu_load( self.alpha * self.sample + (1 - self.alpha) * self.cpu )
            
            # self.cpu_log.append(self.cpu)
            self.dynamics['time'].append(time.time() - start_time)
            self.dynamics['cpu'].append(self.cpu)
            self.dynamics['sleepTimeTarget'].append(self.sleepTimeTarget)
            self.dynamics['sleepTime'].append(self.sleepTime)
            self.dynamics['cpuTarget'].append(self.cpuTarget)


class ControllerThread(Thread):
    """
        Controls the CPU status
    """

    def __init__(self, interval, act_period, ki=None, kp=None):
        # synchronization
        self.shutdown_flag = Event()
        self.sleep_lock = RLock()
        self.cpu_lock = RLock()
        self.target_lock = RLock()

        self.running = 1  # thread status
        self.sampling_interval = interval
        self.act_period = act_period  # actuation period  in seconds
        self.sleepTime = 0.02   # this is controller output: determines the
                                # sleep time to achieve the requested CPU load
        self.alpha = 0.2  # filter coefficient
        self.CT = 0.20  # target CPU load should be provided as input 
        self.cpu = 0  # current CPU load returned from the Monitor thread
        self.cpuPeriod = 0.03
        if ki is None:
            self.ki = 0.2  # integral constant of th PI regulator
        if kp is None:
            self.kp = 0.02  # proportional constant of th PI regulator
        self.int_err = 0  # integral error
        self.last_ts = time.time()  # last sampled time
        self.err = 0
        super(ControllerThread, self).__init__()
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

    def get_sleep_time(self):
        with self.sleep_lock:
            return self.sleepTime

    def set_sleep_time(self, sleep_time):
        with self.sleep_lock:
            self.sleepTime = sleep_time

    def get_cpu_target(self):
        with self.target_lock:
            return self.CT

    def set_cpu_target(self, CT):
        with self.target_lock:
            self.CT = CT

    def set_cpu(self, cpu):
        with self.cpu_lock:
            # first order filter on the measurement samples
            self.cpu = self.alpha * cpu + (1 - self.alpha) * self.cpu
            

    def get_cpu(self):
        with self.cpu_lock:
            return self.cpu

    def run(self):
        def cpu_model(cpu_period):
            sleep_time = self.act_period - cpu_period
            return sleep_time

        self.resume()
        self.shutdown_flag.clear()
        while not self.shutdown_flag.is_set():
            with self.state:
                if self.paused:
                    self.state.wait()  # Block execution until notified.
                    
            # ControllerThread has to have the same sampling interval as MonitorThread
            time.sleep(self.sampling_interval)

            # get all variables
            with self.target_lock, self.cpu_lock:
                CT = self.CT
                cpu = self.cpu

            # Update target CPU load according to the container cpu_quota
            d_client = docker.from_env()
            myhost = os.uname()[1]
            c = d_client.containers.get(myhost)
            cpu_quota  = c.attrs["HostConfig"]["CpuQuota"]
            cpu_period = c.attrs["HostConfig"]["CpuPeriod"]
            if cpu_period <= 0: cpu_period = 100000
            if cpu_quota  <= 0: cpu_quota  = 100000
            sys_quota_perc = cpu_quota / cpu_period
            CT = CT * sys_quota_perc

            self.err = CT - cpu * 0.01  # computes the proportional error
            ts = time.time()

            samp_int = ts - self.last_ts  # sample interval
            self.int_err = self.int_err + self.err * samp_int  # computes the
            #  integral error
            self.last_ts = ts
            self.cpuPeriod = self.kp * self.err + self.ki * self.int_err

            # anti wind up control
            if self.cpuPeriod < 0:
                self.cpuPeriod = 0
                self.int_err = self.int_err - self.err * samp_int
            if self.cpuPeriod > self.act_period:
                self.cpuPeriod = self.act_period
                self.int_err = self.int_err - self.err * samp_int

            self.set_sleep_time(cpu_model(self.cpuPeriod))


class MyClosedLoopActuator(Thread):
    """
        Generates CPU load by tuning the sleep time
    """

    def __init__(self, controller:ControllerThread, monitor:MonitorThread, act_period, duration, target):
        self.controller = controller
        self.monitor = monitor
        self.duration = duration
        self.target = target
        self.controller.set_cpu(self.monitor.get_cpu_load())
        self.act_period = act_period  # actuation period  in seconds
        self.start_time = time.time()
        self.shutdown_flag = Event()
        super(MyClosedLoopActuator, self).__init__()
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


    def generate_load(self, sleep_time):
        interval = time.time() + self.act_period - sleep_time
        # print(f'{interval-time.time():.3f} - {self.period:.3f} - {sleep_time:.3f}')
        # generates some getCpuLoad for interval seconds
        while time.time() < interval:
            pr = 213123  # generates some load
            _ = pr * pr
            pr = pr + 1

        time.sleep(sleep_time)


    def run(self):
        self.resume()

        sleep_time = 0
        self.shutdown_flag.clear()
        while not self.shutdown_flag.is_set():
            with self.state:
                if self.paused:
                    self.state.wait()  # Block execution until notified.
            self.controller.set_cpu(self.monitor.get_cpu_load())
            sleep_time = self.controller.get_sleep_time()
            self.generate_load(sleep_time)
            # self.send_plot_sample()


class CpuFollowThroughput(Thread):
    """
        Set the target CPU accordingly to the received throughput on 'ogstun' interface 
    """

    def __init__(self, control:ControllerThread, monitor:MonitorThread, actuator:MyClosedLoopActuator, sample_period):
        self.control = control
        self.monitor    = monitor
        self.actuator   = actuator
        self.shutdown_flag = Event()
        self.sample_period = sample_period
        self.last_rx_traffic = 0
        self.last_rx_tsample = 0
        super(CpuFollowThroughput, self).__init__()
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

    def get_traffic_sample( self ):
        sample = psutil.net_io_counters(pernic=True)
        return sample["ogstun"].bytes_recv, time.time()

    def calc_bitrate( self ):
        cur_rx_traffic, cur_sample_time = self.get_traffic_sample()
        bit_rate = (cur_rx_traffic-self.last_rx_traffic) * 8 / 1e6 / (cur_sample_time-self.last_rx_tsample)
        self.last_rx_traffic = cur_rx_traffic
        self.last_rx_tsample = cur_sample_time
        return bit_rate


    def run(self):
        self.resume()
        self.shutdown_flag.clear()
        self.last_rx_traffic,self.last_rx_tsample = self.get_traffic_sample()

        while not self.shutdown_flag.is_set():
            with self.state:
                if self.paused:
                    self.state.wait()  # Block execution until notified.
            time.sleep(self.sample_period)
            bitrate = self.calc_bitrate()
            cpu_load = bitrate*0.01  # 1% of CPU for each Mpbs 
            # print(time.time())
            if bitrate > 0:
                self.control.set_cpu_target( cpu_load )
                self.monitor.resume()
                self.control.resume()
                self.actuator.resume()
            else:
                self.monitor.pause()
                self.control.pause()
                self.actuator.pause()
        self.monitor.pause()
        self.control.pause()
        self.actuator.pause()


def load_cpu(monitor:MonitorThread, control:ControllerThread, actuator:MyClosedLoopActuator, load:float):
    if load > 0:
        control.set_cpu_target(load)
        monitor.resume()
        control.resume()
        actuator.resume()
    else:
        monitor.pause()
        control.pause()
        actuator.pause()


def main( argv ):
    # redis_ip = argv[1]
    
    d_cli = docker.from_env()
    redis_ip = d_cli.containers.get("my-redis").attrs['NetworkSettings']['IPAddress']

    r = redis.StrictRedis(host=redis_ip, port=6379, password="", decode_responses=True)

    c_name = os.getenv('COMPONENT_NAME')

    rp = r.pubsub()
    rp.subscribe(f'{c_name}_cpu_stress',f'{c_name}_cpu_load','start_cpu_follow_throughput','stop_cpu_follow_throughput')

    target_core = 0
    sampling_interval = 0.2
    target_load = 0
    duration_seconds = None
    actuation_period = 0.05

    # # lock this process to the target core
    # process = psutil.Process(os.getpid())
    # process.cpu_affinity([target_core])

    monitor = MonitorThread(target_core, sampling_interval)
    control = ControllerThread(sampling_interval, actuation_period)
    control.set_cpu_target(target_load)

    actuator = MyClosedLoopActuator(control, monitor, actuation_period, duration_seconds, target_core)

    monitor.start()
    control.start()
    actuator.start()
    monitor.pause()
    control.pause()
    actuator.pause()

    while True:
        message = rp.get_message()

        for message in rp.listen():
            
            if message["type"] == "subscribe":
                continue

            if message["channel"] == f'{c_name}_cpu_stress':
                if message["data"] == "start":
                    os.system("sysbench --test=cpu --max-time=20 run &" )
                elif message["data"] == "stop":
                    os.system("python3 /mnt/volume_util/pskill.py sysbench" )
                else:
                    pass

            if message["channel"] == f'{c_name}_cpu_load':
                print( "Init load" )
                load_cpu( monitor, control, actuator, float(message["data"]) )

            if message["channel"] == "start_cpu_follow_throughput":
                cpu_follow_thr = CpuFollowThroughput(control, monitor, actuator, 0.5)
                cpu_follow_thr.start()

            if message["channel"] == "stop_cpu_follow_throughput":
                cpu_follow_thr.stop()
                cpu_follow_thr.join()



if __name__ == '__main__':
    main( sys.argv )
