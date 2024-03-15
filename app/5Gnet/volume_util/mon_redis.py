#!/usr/bin/env python3

import redis, docker, os
from redis.client import PubSub
import sys, time, psutil


def get_intf_sample():
    # val = psutil.net_io_counters(pernic=True,nowrap=True)
    val = psutil.net_io_counters(pernic=True)

    return val["ogstun"].bytes_recv , time.time()


def mon_intf(r, rp:PubSub , host_name, last_sample_traffic , last_sample_time):

    while True:
        cur_traffic , cur_sample_time = get_intf_sample()
        bit_rate = (cur_traffic-last_sample_traffic) * 8 / 1e6 / (cur_sample_time-last_sample_time)
        r.ts().add(f'{host_name}:ogstun_recv', "*", bit_rate ) # automatic timestamp in ms

        last_sample_traffic = cur_traffic
        last_sample_time    = cur_sample_time

        message = rp.get_message()
        if message:
            if message["type"] == "subscribe":
                continue
            if message["channel"] == "throughput_monitoring":
                if message['data'] == "stop":
                    wait_command_loop(r, rp, host_name)

        time.sleep(1)


def wait_command_loop(r, rp:PubSub , hostname):
    last_sample_traffic = 0
    last_sample_time    = 0
    for message in rp.listen():
        if message["type"] == "subscribe":
            continue
        if message["channel"] == "throughput_monitoring":
            if message['data'] == "start":
                last_sample_traffic , last_sample_time = get_intf_sample()
                mon_intf(r, rp,hostname,last_sample_traffic , last_sample_time)


def main():
    host_name = os.getenv('COMPONENT_NAME')

    d_cli = docker.from_env()
    redis_ip = d_cli.containers.get("my-redis").attrs['NetworkSettings']['IPAddress']

    r = redis.StrictRedis(host=redis_ip, port=6379, password="", decode_responses=True)

    rp = r.pubsub()
    rp.subscribe('throughput_monitoring')

    wait_command_loop( r, rp , host_name )


if __name__ == "__main__":
    main()
