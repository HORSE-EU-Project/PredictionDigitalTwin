from mininet.net import Mininet
from mininet.link import TCLink
from mininet.node import OVSController
from mininetFastAPI import MininetRest
from mininet.topo import SingleSwitchTopo
from comnetsemu.net import Containernet, VNFManager
from comnetsemu.cli import CLI

import os, time
from multiprocessing import Process
from multiprocessing import active_children

net = Containernet(topo=SingleSwitchTopo(k=2),controller=OVSController,link=TCLink)

net.start()

processid = os.fork()
print (" Process ID: " + str(processid))

if processid >0:
    mininet_rest = MininetRest(net)
    mininet_rest.run()
    print('INFO:     Main waiting for childs to terminate...')
    time.sleep(2)
    # get all active child processes
    active = active_children()
    print(f'INFO:    Active Children: {len(active)}')
    # terminate all active children
    for child in active:
        child.kill()
    # block until all children have closed
    for child in active:
        child.join()
    # report active children
    active = active_children()
    print(f'INFO:    Active Children: {len(active)}')
else:
    time.sleep(2)
    CLI(net)
    net.stop()

