<img src="./images/HORSE-logo.jpg" title="./images/HORSE-logo.jpg" width=1000px></img>

HORSE Prediction and Prevention Digital Twin
============================================
*This is the official repository of the Prediction and Prevention Digital Twin developed within the [HORSE SNS JU project](https://horse-6g.eu).

The Prediction and Prevention Digital Twin is a Network Digital Twin built within a single Virtual Machine for compactness.
It can be run on any PC platform via Vagrant and Virtualbox.

The purpose of the Network Digital Twin is to:
- Emulate a 5G network deployment in comnetsemu.
- Provide REST APIs to control and interact with the Digital Twin engine (for Prediction and Prevention purposes).

Supported open source software:
- Comnetsemu: v0.3.0
- UERANSIM: v3.2.6
- Open5gs: v2.4.2
- PyMongo
- Tabulate
- PyFiGlet

## Install instructions

Once the Comnetsemu environment is correctly running, Build the necessary docker images for 5G UERANSIM and Open5GS and other software:
```
./install.sh
```
or alternatively build the containers by using the build/build.sh command.

To be able to capture traffic, you need to enable vagrant to use sudo without password.
This is done by the following command:
```
sudo visudo
```
and then by putting the following line after the root attributes:
```
vagrant ALL=(ALL:ALL) NOPASSWD: ALL
```

## Run instructions

For interactive operation, please run the following commands in different terminals.

Start Network Digital Twin with Ryu controller and sFlow:
```
./runDigitalTwin.sh
```

Run the web-based GUI to interact with the Digital Twin (for testing purposes):
```
cd GUI
./launch
```

If you want to test interfaces, too:
```
cd customization
./run_ntfy.sh
```

When you quit the NDT, please clean up:
```
./clean.sh
```

## Test instructions

To check that the installation of Comnetsemu (see Comnetsemu Build Instructions below) is correct, run:
```
sudo make test
```
in the comnetsemu/ directory.

To check that the NDT is running correctly, run:
```
./5g_wait_for_healthy.sh
```

## Used ports

| Service | Port | Notes |
| :-------- | :-------: | :------ |
| Digital Twin GUI | 8501 |  |
| Digital Twin API | 8000 | (8000/docs for Swagger) |
| Open5GS Core | 3000 -> 1234| (user: admin, password: 1423) |
| sFlow | 8008 | if active |
| VSCode server | 8888 | to be installed and run manually (password: password) |
| NTFY server | 80 -> 8086 | to be run manually |
| Wireshark server | 80 -> 8085 | to be run manually |
| Reserved by Open5GS | 1235 | |

## Comnetsemu Build Instructions

First, from the host machine, install the original comnetsemu VM:
```bash
$ cd ~
$ git clone https://github.com/HORSE-EU-Project/PredictionDigitalTwin.git
$ cd ./PredictionDigitalTwin
$ vagrant up NDT
# Take a coffee and wait about 15-20 minutes

# SSH into the VM when it's up and ready (The ComNetsEmu banner is printed on the screen)
$ vagrant ssh NDT
```

In case Ryu controller does not work properly, please run:
```
pip install dnspython==2.2.1
```

Be sure that the additional libraries are provided in the vm_provisioning.sh script in the /util directory.


## Useful information about the HORSE Network Digital Twin

### The HORSE reference network topology and 5GS setup

#### Reference HORSE deployment scenario

The following briefly illustrates the default HORSE deployment scenario.

<img src="./HORSE_data/newTopology.png" title="HORSE Default topology" width=1000px></img>

#### Original deployment scenario

This was the original scenario, that includes 5 DockerHosts as shown in the figure below.
The UE starts two PDU session one for each slice defined in the core network.
This picture is provided to describe the configuration of the 5GS and related IP assignments.

<img src="./images/topology.jpg" title="./images/topology.jpg" width=1000px></img>

To configure the 5GC, we can open the WebUI by opening the following page in a browser on the host OS.
```
http://<VM_IP>:3000/
```

### Check UE connections

Notice how the UE DockerHost has been initiated running `open5gs_ue_init.sh` which, based on the configuration provided in `open5gs-ue.yaml`, creates two default UE connections.
The sessions are started specifying the slice, not the APN. The APN, and thus the associated UPF, is selected by the 5GC since, in `subscriber_profile.json`, a slice is associated to a session with specific DNN.

Enter the container and verify UE connections:

``` 
$ ./enter_container.sh ue1
# ifconfig
``` 

or

```
$ ./enter_container.sh ue1
# ifconfig
```

You should see interfaces uesimtun0 (for the upf_cld) and uesimtun1 (for the upf_mec), or similar, active.

```
uesimtun0: flags=369<UP,POINTOPOINT,NOTRAILERS,RUNNING,PROMISC>  mtu 1400
        inet 10.45.0.2  netmask 255.255.255.255  destination 10.45.0.2
        unspec 00-00-00-00-00-00-00-00-00-00-00-00-00-00-00-00  txqueuelen 500  (UNSPEC)
        RX packets 0  bytes 0 (0.0 B)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 0  bytes 0 (0.0 B)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

uesimtun1: flags=369<UP,POINTOPOINT,NOTRAILERS,RUNNING,PROMISC>  mtu 1400
        inet 10.46.0.2  netmask 255.255.255.255  destination 10.46.0.2
        unspec 00-00-00-00-00-00-00-00-00-00-00-00-00-00-00-00  txqueuelen 500  (UNSPEC)
        RX packets 0  bytes 0 (0.0 B)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 0  bytes 0 (0.0 B)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
```


Start a ping test to check connectivity:
``` 
# ping -c 3 -n -I uesimtun0 www.google.com
# ping -c 3 -n -I uesimtun1 www.google.com
``` 

### Test the environment

You can run tcpdump software to test correct routing of traffic to the related 5G slices:

``` 
$ ./start_tcpdump.sh upf
``` 

#### Latency test
Enter in the UE container:
``` 
$ ./enter_container.sh ue
``` 

Start ping test on the interfaces related to the two slices:
``` 
# ping -c 3 -n -I uesimtun0 10.45.0.1
# ping -c 3 -n -I uesimtun1 10.46.0.1
``` 

Observe the Round Trip Time using uesimtun0 (slice 1 - reaching the UPF in the "cloud DC" with DNN="internet" ) and ueransim1 (slice 2 - reaching the UPF in the 'mec DC' with DNN="mec")


#### Bandwidth test

Enter in the UE container:
``` 
$ ./enter_container.sh ue1
``` 

Start bandwidth test leveraging the two slices:
``` 
# iperf3 -c 10.45.0.1 -B 10.45.0.2 -t 5
# iperf3 -c 10.46.0.1 -B 10.46.0.2 -t 5
``` 

Observe how the data-rate in the two cases follows the maximum data-rate specified for the two slices (2 Mbps for sst 1 and 10Mbps for sst 2).


### Contact

Main maintainer:
- Fabrizio Granelli - fabrizio.granelli@unitn.it

Special Acknowledgements to:
- Riccardo Fedrizzi - rfedrizzi@fbk.eu
for the original UERANSIM/Open5Gs port

- Bennati Jacopo
- Finetti Emiliano
- Arrondo Diego
for the updated UERANSIM/Open5Gs implementation. See [original README.md file](./README_5g_network.md).


