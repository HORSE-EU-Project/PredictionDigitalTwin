#!/usr/bin/python

#
#  A simple Python TWAMP implementation
#

# import the required libraries
import os
import struct
import sys
import time
import socket
import logging
import binascii
import threading
import random
import argparse
import signal
import select

if (sys.platform == "win32"):
    time0 = time.time() - time.clock()

if sys.version_info > (3,):
    long = int

# Constants to convert between python timestamps and NTP 8B binary format [RFC1305]
TIMEOFFSET = long(2208988800)    # Time Difference: 1-JAN-1900 to 1-JAN-1970
ALLBITS = long(0xFFFFFFFF)       # To calculate 32bit fraction of the second

# current time acquisition
def now():
    if (sys.platform == "win32"):
        return time.clock() + time0
    return time.time()

# NTP time conversion to python
def time_ntp2py(data):

    ta, tb = struct.unpack('!2I', data)
    t = ta - TIMEOFFSET + float(tb) / float(ALLBITS)
    return t

def zeros(nbr):
    return struct.pack('!%sB' % nbr, *[0 for x in range(nbr)])

# time conversions
def dp(ms):
    if abs(ms) > 60000:
        return "%.2fmin" % float(ms / 60000)
    if abs(ms) > 10000:
        return "%.2fsec" % float(ms / 1000)
    if abs(ms) > 1000:
        return "%.2fsec" % float(ms / 1000)
    if abs(ms) > 1:
        return "%.2fms" % ms
    return "%dus" % long(ms * 1000)

# parse IP address
def parse_addr(addr, default_port=20000):
    if addr == '':
        # no address given (default: localhost IPv4 or IPv6)
        return "", default_port, 0
    elif ']:' in addr:
        # IPv6 address with port
        ip, port = addr.rsplit(':', 1)
        return ip.strip('[]'), int(port), 6
    elif ']' in addr:
        # IPv6 address without port
        return addr.strip('[]'), default_port, 6
    elif addr.count(':') > 1:
        # IPv6 address without port
        return addr, default_port, 6
    elif ':' in addr:
        # IPv4 address with port
        ip, port = addr.split(':')
        return ip, int(port), 4
    else:
        # IPv4 address without port
        return addr, default_port, 4

# UDP session management
class udpSession(threading.Thread):

    def __init__(self, addr="", port=20000, tos=0, ttl=64, do_not_fragment=False, ipversion=4):
        threading.Thread.__init__(self)
        if ipversion == 6:
            self.bind6(addr, port, tos, ttl)
        else:
            self.bind(addr, port, tos, ttl, do_not_fragment)
        self.running = True

    def bind(self, addr, port, tos, ttl, df):
        log.debug(
            "bind(addr=%s, port=%d, tos=%d, ttl=%d)", addr, port, tos, ttl)
        self.socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, tos)
        self.socket.setsockopt(socket.SOL_IP,     socket.IP_TTL, ttl)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((addr, port))
        if df:
            if (sys.platform == "linux2"):
                self.socket.setsockopt(socket.SOL_IP, 10, 2)
            elif (sys.platform == "win32"):
                self.socket.setsockopt(socket.SOL_IP, 14, 1)
            elif (sys.platform == "darwin"):
                log.error("do-not-fragment can not be set on darwin")
            else:
                log.error("unsupported OS, ignore do-not-fragment option")
        else:
            if (sys.platform == "linux2"):
                self.socket.setsockopt(socket.SOL_IP, 10, 0)

    def bind6(self, addr, port, tos, ttl):
        log.debug(
            "bind6(addr=%s, port=%d, tos=%d, ttl=%d)", addr, port, tos, ttl)
        self.socket = socket.socket(
            socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_TCLASS, tos)
        self.socket.setsockopt(
            socket.IPPROTO_IPV6, socket.IPV6_UNICAST_HOPS, ttl)
        self.socket.setsockopt(socket.SOL_SOCKET,   socket.SO_REUSEADDR, 1)
        self.socket.bind((addr, port))
        log.info("Wait to receive test packets on [%s]:%d", addr, port)

    def sendto(self, data, address):
        log.debug("transmit: %s", binascii.hexlify(data))
        self.socket.sendto(data, address)

    def recvfrom(self):
        data, address = self.socket.recvfrom(9216)
        log.debug("received: %s", binascii.hexlify(data))
        return data, address

    def stop(self, signum, frame):
        log.info("SIGINT received: Stop TWL session reflector")
        self.running = False
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()

# TWAMP statistics management
class twampStatistics():

    def __init__(self):
        self.count = 0

    # adding values
    def add(self, delayRT, delayOB, delayIB, rseq, sseq):
        if self.count == 0:
            self.minOB = delayOB
            self.minIB = delayIB
            self.minRT = delayRT

            self.maxOB = delayOB
            self.maxIB = delayIB
            self.maxRT = delayRT

            self.sumOB = delayOB
            self.sumIB = delayIB
            self.sumRT = delayRT

            self.lossIB = rseq
            self.lossOB = sseq - rseq

            self.jitterOB = 0
            self.jitterIB = 0
            self.jitterRT = 0

            self.lastOB = delayOB
            self.lastIB = delayIB
            self.lastRT = delayRT
        else:
            self.minOB = min(self.minOB, delayOB)
            self.minIB = min(self.minIB, delayIB)
            self.minRT = min(self.minRT, delayRT)

            self.maxOB = max(self.maxOB, delayOB)
            self.maxIB = max(self.maxIB, delayIB)
            self.maxRT = max(self.maxRT, delayRT)

            self.sumOB += delayOB
            self.sumIB += delayIB
            self.sumRT += delayRT

            self.lossIB = rseq - self.count
            self.lossOB = sseq - rseq

            if self.count == 1:
                self.jitterOB = abs(self.lastOB - delayOB)
                self.jitterIB = abs(self.lastIB - delayIB)
                self.jitterRT = abs(self.lastRT - delayRT)
            else:
                self.jitterOB = self.jitterOB + \
                    (abs(self.lastOB - delayOB) - self.jitterOB) / 16
                self.jitterIB = self.jitterIB + \
                    (abs(self.lastIB - delayIB) - self.jitterIB) / 16
                self.jitterRT = self.jitterRT + \
                    (abs(self.lastRT - delayRT) - self.jitterRT) / 16

            self.lastOB = delayOB
            self.lastIB = delayIB
            self.lastRT = delayRT

        self.count += 1

    # TWAMP results displayed on the terminal
    def dump(self, total):

        print("===============================================================================")
        print("Direction\tMin\tMax\tAvg\tJitter\tLoss")
        print("-------------------------------------------------------------------------------")
        if self.count > 0:
            self.lossRT = total - self.count
            print("  Outbound: \t%s\t%s\t%s\t%s\t%5.1f%%" % (dp(self.minOB), dp(self.maxOB), dp(self.sumOB / self.count), dp(self.jitterOB), 100 * float(self.lossOB) / total))
            print("  Inbound:  \t%s\t%s\t%s\t%s\t%5.1f%%" % (dp(self.minIB), dp(self.maxIB), dp(self.sumIB / self.count), dp(self.jitterIB), 100 * float(self.lossIB) / total))
            print("  Roundtrip:\t%s\t%s\t%s\t%s\t%5.1f%%" % (dp(self.minRT), dp(self.maxRT), dp(self.sumRT / self.count), dp(self.jitterRT), 100 * float(self.lossRT) / total))
        else:
            print("  NO STATS AVAILABLE (100% loss)")
        print("===============================================================================")
        sys.stdout.flush()

# TWAMP session management - sender
class twampSessionSender(udpSession):

    def __init__(self, args):
        # Session Sender / Session Reflector:
        #   get Address, UDP port, IP version from near_end/far_end attributes
        sip, spt, sipv = parse_addr(args.near_end, 20000)
        rip, rpt, ripv = parse_addr(args.far_end,  20001)

        ipversion = 6 if (sipv == 6) or (ripv == 6) else 4
        udpSession.__init__(self, sip, spt, args.tos, args.ttl, args.do_not_fragment, ipversion)

        self.remote_addr = rip
        self.remote_port = rpt
        self.interval = float(args.interval) / 1000
        self.count = args.count
        self.stats = twampStatistics()

        if args.padding != -1:
            self.padmix = [args.padding]
        elif ipversion == 6:
            self.padmix = [0, 0, 0, 0, 0, 0, 0, 514, 514, 514, 514, 1438]
        else:
            self.padmix = [8, 8, 8, 8, 8, 8, 8, 534, 534, 534, 534, 1458]

    def run(self):
        schedule = now()
        endtime = schedule + self.count * self.interval + 5

        idx = 0
        while self.running:
            while select.select([self.socket], [], [], 0)[0]:
                t4 = now()
                data, address = self.recvfrom()

                if len(data) < 36:
                    log.error("short packet received: %d bytes", len(data))
                    continue

                t3 = time_ntp2py(data[4:12])
                t2 = time_ntp2py(data[16:24])
                t1 = time_ntp2py(data[28:36])

                delayRT = max(0, 1000 * (t4 - t1 + t2 - t3))  # round-trip delay
                delayOB = max(0, 1000 * (t2 - t1))            # out-bound delay
                delayIB = max(0, 1000 * (t4 - t3))            # in-bound delay

                rseq = struct.unpack('!I', data[0:4])[0]
                sseq = struct.unpack('!I', data[24:28])[0]

                log.info("Reply from %s [rseq=%d sseq=%d rtt=%.2fms outbound=%.2fms inbound=%.2fms]", address[0], rseq, sseq, delayRT, delayOB, delayIB)
                self.stats.add(delayRT, delayOB, delayIB, rseq, sseq)

                if sseq + 1 == self.count:
                    log.info("All packets received back")
                    self.running = False

            t1 = now()
            if (t1 >= schedule) and (idx < self.count):
                schedule = schedule + self.interval

                data = struct.pack('!L2IH', idx, long(TIMEOFFSET + t1), long((t1 - long(t1)) * ALLBITS), 0x3fff)
                pbytes = zeros(self.padmix[long(len(self.padmix) * random.random())])

                self.sendto(data + pbytes, (self.remote_addr, self.remote_port))
                log.info("Sent to %s [sseq=%d]", self.remote_addr, idx)

                idx = idx + 1
                if schedule > t1:
                    r, w, e = select.select([self.socket], [], [], schedule - t1)

            if (t1 > endtime):
                log.info("Receive timeout for last packet (don't wait anymore)")
                self.running = False

        self.stats.dump(idx)

# TWAMP session management - reflector
class twampSessionReflector(udpSession):

    def __init__(self, args):
        addr, port, ipversion = parse_addr(args.near_end, 20001)

        if args.padding != -1:
            self.padmix = [args.padding]
        elif ipversion == 6:
            self.padmix = [0, 0, 0, 0, 0, 0, 0, 514, 514, 514, 514, 1438]
        else:
            self.padmix = [8, 8, 8, 8, 8, 8, 8, 534, 534, 534, 534, 1458]

        udpSession.__init__(self, addr, port, args.tos, args.ttl, args.do_not_fragment, ipversion)

    def run(self):
        index = {}
        reset = {}

        while self.running:
            try:
                data, address = self.recvfrom()

                t2 = now()
                sec = long(TIMEOFFSET + t2)             # seconds since 1-JAN-1900
                msec = long((t2 - long(t2)) * ALLBITS)  # 32bit fraction of the second

                sseq = struct.unpack('!I', data[0:4])[0]
                t1 = time_ntp2py(data[4:12])

                log.info("Request from %s:%d [sseq=%d outbound=%.2fms]", address[0], address[1], sseq, 1000 * (t2 - t1))

                idx = 0
                if address not in index.keys():
                    log.info("set rseq:=0     (new remote address/port)")
                elif reset[address] < t2:
                    log.info("reset rseq:=0   (session timeout, 30sec)")
                elif sseq == 0:
                    log.info("reset rseq:=0   (received sseq==0)")
                else:
                    idx = index[address]

                rdata = struct.pack('!L2I2H2I', idx, sec, msec, 0x001, 0, sec, msec)
                pbytes = zeros(self.padmix[long(len(self.padmix) * random.random())])
                self.sendto(rdata + data[0:14] + pbytes, address)

                index[address] = idx + 1
                reset[address] = t2 + 30  # timeout is 30sec

            except Exception as e:
                log.debug('Exception: %s', str(e))
                break

        log.info("TWL session reflector stopped")

# TWAMP session management - client
class twampControlClient:

    def __init__(self, server="", tcp_port=862, tos=0x88, ipversion=4):
        if ipversion == 6:
            self.connect6(server, tcp_port, tos)
        else:
            self.connect(server, tcp_port, tos)

    def connect(self, server="", port=862, tos=0x88):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, tos)
        self.socket.connect((server, port))

    def connect6(self, server="", port=862, tos=0x88):
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_TCLASS, tos)
        self.socket.connect((server, port))

    def send(self, data):
        log.debug("CTRL.TX %s", binascii.hexlify(data))
        try:
            self.socket.send(data)
        except Exception as e:
            log.critical('*** Sending data failed: %s', str(e))

    def receive(self):
        data = self.socket.recv(9216)
        log.debug("CTRL.RX %s (%d bytes)", binascii.hexlify(data), len(data))
        return data

    def close(self):
        self.socket.close()

    def connectionSetup(self):
        log.info("CTRL.RX <<Server Greeting>>")
        data = self.receive()
        self.smode = struct.unpack('!I', data[12:16])[0]
        log.info("TWAMP modes supported: %d", self.smode)
        if self.smode & 1 == 0:
            log.critical('*** Software only supports unauthenticated mode(1)')

        log.info("CTRL.TX <<Setup Response>>")
        self.send(struct.pack('!I', 1) + zeros(160))

        log.info("CTRL.RX <<Server Start>>")
        data = self.receive()

        rval = ord(data[15])
        if rval != 0:
            # TWAMP setup request not accepted by server
            log.critical("*** ERROR CODE %d in <<Server Start>>", rval)

        self.nbrSessions = 0

    def reqSession(self, sender="", s_port=20001, receiver="", r_port=20002, startTime=0, timeOut=3, dscp=0, padding=0):
        typeP = dscp << 24

        if startTime != 0:
            startTime += now() + TIMEOFFSET

        if sender == "":
            request = struct.pack('!4B L L H H 13L 4ILQ4L', 5, 4, 0, 0, 0, 0, s_port, r_port, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, padding, startTime, 0, timeOut, 0, typeP, 0, 0, 0, 0, 0)
        elif sender == "::":
            request = struct.pack('!4B L L H H 13L 4ILQ4L', 5, 6, 0, 0, 0, 0, s_port, r_port, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, padding, startTime, 0, timeOut, 0, typeP, 0, 0, 0, 0, 0)
        elif ':' in sender:
            s = socket.inet_pton(socket.AF_INET6, sender)
            r = socket.inet_pton(socket.AF_INET6, receiver)
            request = struct.pack('!4B L L H H 16s 16s 4L L 4ILQ4L', 5, 6, 0, 0, 0, 0, s_port, r_port, s, r, 0, 0, 0, 0, padding, startTime, 0, timeOut, 0, typeP, 0, 0, 0, 0, 0)
        else:
            s = socket.inet_pton(socket.AF_INET, sender)
            r = socket.inet_pton(socket.AF_INET, receiver)
            request = struct.pack('!4B L L H H 16s 16s 4L L 4ILQ4L', 5, 4, 0, 0, 0, 0, s_port, r_port, s, r, 0, 0, 0, 0, padding, startTime, 0, timeOut, 0, typeP, 0, 0, 0, 0, 0)

        log.info("CTRL.TX <<Request Session>>")
        self.send(request)
        log.info("CTRL.RX <<Session Accept>>")
        data = self.receive()

        rval = ord(data[0])
        if rval != 0:
            log.critical("ERROR CODE %d in <<Session Accept>>", rval)
            return False
        return True

    def startSessions(self):
        request = struct.pack('!B', 2) + zeros(31)
        log.info("CTRL.TX <<Start Sessions>>")
        self.send(request)
        log.info("CTRL.RX <<Start Accept>>")
        self.receive()

    def stopSessions(self):
        request = struct.pack('!BBHLQQQ', 3, 0, 0, self.nbrSessions, 0, 0, 0)
        log.info("CTRL.TX <<Stop Sessions>>")
        self.send(request)

        self.nbrSessions = 0

# TWAMP responder
def twl_responder(args):
    reflector = twampSessionReflector(args)
    #reflector.setDaemon(True)
    #reflector.setName("twl_responder")
    reflector.start()

    signal.signal(signal.SIGINT, reflector.stop)

    while reflector.is_alive():
        time.sleep(0.1)

# TWAMP sender
def twl_sender(args):
    sender = twampSessionSender(args)
    #sender.setDaemon(True)
    #sender.setName("twl_responder")
    sender.start()

    signal.signal(signal.SIGINT, sender.stop)

    while sender.is_alive():
        time.sleep(0.1)

# TWAMP controller
def twamp_controller(args):
    sip, spt, ipv = parse_addr(args.near_end, 20000)
    rip, rpt, ipv = parse_addr(args.far_end,  20001)

    client = twampControlClient(server=rip, ipversion=ipv)
    client.connectionSetup()

    if client.reqSession(s_port=spt, r_port=rpt):
        client.startSessions()

        sender = twampSessionSender(args)
        sender.setDaemon(True)
        sender.setName("twl_responder")
        sender.start()
        signal.signal(signal.SIGINT, sender.stop)

        while sender.isAlive():
            time.sleep(0.1)
        time.sleep(5)

        client.stopSessions()

# TWAMP Session Sender / Reflector
def twamp_ctclient(args):
    sip, spt, ipv = parse_addr(args.twl_send, 20000)
    rip, rpt, ipv = parse_addr(args.twserver, 20001)

    client = twampControlClient(server=rip, ipversion=ipv)
    client.connectionSetup()

    if client.reqSession(sender=sip, s_port=spt, receiver="0.0.0.0", r_port=rpt):
        client.startSessions()

        while True:
            time.sleep(0.1)

        client.stopSessions()

#############################################################################

dscpmap = {"be":   0, "cp1":   1,  "cp2":  2,  "cp3":  3, "cp4":   4, "cp5":   5, "cp6":   6, "cp7":   7,
           "cs1":  8, "cp9":   9, "af11": 10, "cp11": 11, "af12": 12, "cp13": 13, "af13": 14, "cp15": 15,
           "cs2": 16, "cp17": 17, "af21": 18, "cp19": 19, "af22": 20, "cp21": 21, "af23": 22, "cp23": 23,
           "cs3": 24, "cp25": 25, "af31": 26, "cp27": 27, "af32": 28, "cp29": 29, "af33": 30, "cp31": 31,
           "cs4": 32, "cp33": 33, "af41": 34, "cp35": 35, "af42": 36, "cp37": 37, "af43": 38, "cp39": 39,
           "cs5": 40, "cp41": 41, "cp42": 42, "cp43": 43, "cp44": 44, "cp45": 45, "ef":   46, "cp47": 47,
           "nc1": 48, "cp49": 49, "cp50": 50, "cp51": 51, "cp52": 52, "cp53": 53, "cp54": 54, "cp55": 55,
           "nc2": 56, "cp57": 57, "cp58": 58, "cp59": 59, "cp60": 60, "cp61": 61, "cp62": 62, "cp63": 63}
           
if __name__ == '__main__':
    debug_parser = argparse.ArgumentParser(add_help=False)

    debug_options = debug_parser.add_argument_group("Debug Options")
    debug_options.add_argument('-l', '--logfile', metavar='filename', type=argparse.FileType('wb', 0), default='-', help='Specify the logfile (default: <stdout>)')
    group = debug_options.add_mutually_exclusive_group()
    group.add_argument('-q', '--quiet',   action='store_true', help='disable logging')
    group.add_argument('-v', '--verbose', action='store_true', help='enhanced logging')
    group.add_argument('-d', '--debug',   action='store_true', help='extensive logging')

    ipopt_parser = argparse.ArgumentParser(add_help=False)
    group = ipopt_parser.add_argument_group("IP socket options")
    group.add_argument('--tos',     metavar='type-of-service', default=0x88, type=int, help='IP TOS value')
    group.add_argument('--dscp',    metavar='dscp-value', help='IP DSCP value')
    group.add_argument('--ttl',     metavar='time-to-live', default=64,   type=int, help='[1..128]')
    group.add_argument('--padding', metavar='bytes', default=0,    type=int, help='IP/UDP mtu value')
    group.add_argument('--do-not-fragment',  action='store_true', help='keyword (do-not-fragment)')

    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(help='twamp sub-commands')

    p_responder = subparsers.add_parser('responder', help='TWL responder', parents=[debug_parser, ipopt_parser])
    group = p_responder.add_argument_group("TWL responder options")
    group.add_argument('near_end', nargs='?', metavar='local-ip:port', default=":20001")
    group.add_argument('--timer', metavar='value',   default=0,     type=int, help='TWL session reset')

    p_sender = subparsers.add_parser('sender', help='TWL sender', parents=[debug_parser, ipopt_parser])
    group = p_sender.add_argument_group("TWL sender options")
    group.add_argument('far_end', nargs='?', metavar='remote-ip:port', default="127.0.0.1:20001")
    group.add_argument('near_end', nargs='?', metavar='local-ip:port', default=":20000")
    group.add_argument('-i', '--interval', metavar='msec', default=100,  type=int, help="[100,1000]")
    group.add_argument('-c', '--count',    metavar='packets', default=100,  type=int, help="[1..9999]")

    p_control = subparsers.add_parser('controller', help='TWAMP controller', parents=[debug_parser, ipopt_parser])
    group = p_control.add_argument_group("TWAMP controller options")
    group.add_argument('far_end', nargs='?', metavar='remote-ip:port', default="127.0.0.1:20001")
    group.add_argument('near_end', nargs='?', metavar='local-ip:port', default=":20000")
    group.add_argument('-i', '--interval', metavar='msec', default=100,  type=int, help="[100,1000]")
    group.add_argument('-c', '--count',    metavar='packets', default=100,  type=int, help="[1..9999]")

    p_ctclient = subparsers.add_parser('controlclient', help='TWAMP control client', parents=[debug_parser, ipopt_parser])
    group = p_ctclient.add_argument_group("TWAMP control client options")
    group.add_argument('twl_send', nargs='?', metavar='twamp-sender-ip:port', default="127.0.0.1:20001")
    group.add_argument('twserver', nargs='?', metavar='twamp-server-ip:port', default=":20000")
    group.add_argument('-c', '--count',    metavar='packets', default=100,  type=int, help="[1..9999]")

    # methods to call
    p_sender.set_defaults(parseop=True, func=twl_sender)
    p_control.set_defaults(parseop=True, func=twamp_controller)
    p_ctclient.set_defaults(parseop=True, func=twamp_ctclient)
    p_responder.set_defaults(parseop=True, func=twl_responder)

#############################################################################

    options = parser.parse_args()

    if not options.parseop:
        print(options)
        options.func()
        exit(-1)

# logging levels

    if options.quiet:
        logfile = open(os.devnull, 'a')
        loghandler = logging.StreamHandler(logfile)
        loglevel = logging.NOTSET
    elif options.debug:
        logformat = '%(asctime)s,%(msecs)-3d %(levelname)-8s %(message)s'
        timeformat = '%y/%m/%d %H:%M:%S'
        loghandler = logging.StreamHandler(options.logfile)
        loghandler.setFormatter(logging.Formatter(logformat, timeformat))
        loglevel = logging.DEBUG
    elif options.verbose:
        logformat = '%(asctime)s,%(msecs)-3d %(levelname)-8s %(message)s'
        timeformat = '%y/%m/%d %H:%M:%S'
        loghandler = logging.StreamHandler(options.logfile)
        loghandler.setFormatter(logging.Formatter(logformat, timeformat))
        loglevel = logging.INFO
    else:
        logformat = '%(asctime)s,%(msecs)-3d %(levelname)-8s %(message)s'
        timeformat = '%y/%m/%d %H:%M:%S'
        loghandler = logging.StreamHandler(options.logfile)
        loghandler.setFormatter(logging.Formatter(logformat, timeformat))
        loglevel = logging.WARNING

    log = logging.getLogger("twamp")
    log.setLevel(loglevel)
    log.addHandler(loghandler)

# check DSCP file

    if options.dscp:
        if options.dscp in dscpmap:
            options.tos = dscpmap[options.dscp]
        else:
            parser.error("Invalid DSCP Value '%s'" % options.dscp)

    options.func(options)

# EOF
