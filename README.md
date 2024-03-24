[![MIT Licensed](https://img.shields.io/github/license/stevelorenz/comnetsemu)](https://github.com/stevelorenz/comnetsemu/blob/master/LICENSE)
[![ComNetsEmu CI](https://github.com/stevelorenz/comnetsemu/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/stevelorenz/comnetsemu/actions/workflows/ci.yml)

HORSE Prediction and Prevention Digital Twin
============================================
*This project is based on the virtual emulator/testbed designed for the book:
[Computing in Communication Networks: From Theory to Practice](https://www.amazon.com/Computing-Communication-Networks-Theory-Practice-ebook/dp/B088ZS597R)*

To go straight to the HORSE Prediction and Prevention Digital Twin implementation in the 5GS, please click [HERE](./app/comnetsemu_5Gnet)

**INFO: This project is currently still under development [beta]. Version 1.0.0 has not yet been released.
We try to make it stable but breaking changes might happen.**


## Table of Contents

<!-- vim-markdown-toc GitLab -->

* [Description](#description)
  * [Main Features](#main-features)
* [Installation](#installation)
* [Project Structure](#structure)
* [Contact](#contact)

<!-- vim-markdown-toc -->

## Description

The Network Digital Twin for Prediction and Prevention is a module of the HORSE project architecture.
It is implemented in the ComNetsEmu environment, a testbed and network emulator designed for the NFV/SDN teaching book
["Computing in Communication Networks: From Theory to Practice"](https://www.amazon.com/Computing-Communication-Networks-Theory-Practice-ebook/dp/B088ZS597R).
The design focuses on emulating all examples and applications on a single computer, for example on a laptop.
For more information, please read the documentation about Comnetsemu: [README_comnetsemu.md](README_comnetsemu.md).


### Main Features

-   Use isolated Docker hosts in Mininet topologies.

-   Manage application Docker containers deployed **inside** Docker hosts.
    "Docker-in-Docker" (sibling containers) is used as a lightweight emulation of nested virtualization.
    A Docker host with multiple **internal** Docker containers deployed is used to
	**mimic** an actual physical host running Docker containers (application containers).

-   Implements an end-to-end emulation of the 5GS, using UERANSIM and Open5GS

Check the [Roadmap](./doc/roadmap.md) for planed and WIP features.


## Installation

**Currently, only the latest Ubuntu 20.04 LTS is supported.**
**Supporting multiple Linux distributions and versions is not the goal of this project.**

It is highly recommended to run this software **inside** a virtual machine (VM).
**Root privileges** are required to run the ComNetsEmu/Mininet applications.
It also uses privileged Docker containers by default.
It's also safer to play it inside a VM.
The [installation script](./util/install.sh) is a wrapper of 
an Ansible [playbook](./util/playbooks/install_comnetsemu.yml).
This playbook uses Mininet's install script to install Mininet natively from source.
As described in Mininet's doc, the install script is a bit **intrusive** and may possible **damage** your OS
and/or home directory.
This Network Digital Twin runs smoothly in a VM with 2 vCPUs and 2GB RAM. (Host Physical CPU: Intel i7-7600U @ 2.80GHz).

The recommended and easiest way to create the Prediction and Prevention Digital Twin is to use Vagrant and Virtualbox.
Assuming that the directory where the software is stored is "~/PredictionDigitalTwin" in your home directory, 
just run the following commands to get a fully configured VM using vagrant with Virtualbox provider:

```bash
$ cd ~
$ git clone https://github.com/HORSE-EU-Project/PredictionDigitalTwin.git
$ cd ./PredictionDigitalTwin
$ vagrant up NDT
# Take a coffee and wait about 15-20 minutes

# SSH into the VM when it's up and ready (The ComNetsEmu banner is printed on the screen)
$ vagrant ssh NDT
```

Congratulations! The installation is done successfully!
You can now run the tests, examples, and **skip** the rest of the documentation in this section.

**For users running Windows as the host OS:**

**Warning**: Main developers of ComNetsEmu does not use Windows
and does not have a Windows machine to test on.

1.  If you are using Windows, we recommend using [Mobaxterm](https://mobaxterm.mobatek.net/)
	as the console.
    This should solve problems opening `xterm` in the emulator.

---

The installer will try to install the dependencies using a package manager (apt, pip, etc.)
if the desired version is available.
Unavailable dependencies (e.g. the latest Mininet) and dependencies that require patching
are installed directly from source code.
By default, the dependency source codes are downloaded into `"~/comnetsemu_dependencies"`.
You can modify the Ansible [playbook](./util/playbooks/install_comnetsemu.yml) based on your needs.

Please see the detailed installation guide [here](./doc/installation.md)
for additional installation options.


## Run the Docker-in-Docker example

```bash
$ cd $TOP_DIR/comnetsemu/examples/
$ sudo python3 ./dockerindocker.py
```

See the [README](./examples/README.md) to get information about all built-in examples.

## Project Structure

To keep the VMs small, Vagrantfile and test_containers contain only **minimal** dependencies to start the VMs and be able to run all the built-in examples.
Dependencies of specific applications (e.g. Python packages like numpy, scipy etc.) should be installed by the script or instructions provided in the corresponded application folder.
Therefore, the user need to install them **only if** she or he wants to run that application.

-   [app](./app/): All application programs are classified in this directory.
    Each subdirectory contains a brief introduction, source codes, Dockerfiles for internal containers
	and utility scripts of the application

-   [app/comnetsemu_5Gnet](./app/comnetsemu_5Gnet) Contains the Prediction and Prevention Digital Twin implementation

-   [bin](./bin): Commands and binaries provided by ComNetsEmu

-   [comnetsemu](./comnetsemu/): Source codes of ComNetsEmu's environment Python packages

-   [doc](./doc): Markdown files and sources to generate ComNetsEmu Sphinx documentation

-   [examples](./examples/): Example programs and trials

-   [patch](./patch/): Patches for external dependencies that are installed 
    from source code via [installer](./util/install.sh)

-   [test_containers](./test_containers/): Contains Dockerfiles for essential Docker images
    for tests and built-in examples

-   [utils](./util/): Utility and helper scripts

-   [Vagrantfile](./Vagrantfile): Vagrant file to setup development/experiment VM environment


## FAQ

Check [faq](./doc/faq.md)


## Contact

Project main maintainers:

- Fabrizio Granelli (CNIT, U. Trento): fabrizio.granelli@unitn.it
