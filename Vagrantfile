# -*- mode: ruby -*-
# vi: set ft=ruby :
# About: Vagrant file for the development environment

###############
#  Variables  #
###############

CPUS = 2
# - 2GB RAM SHOULD be sufficient for most examples and applications.
# - Currently only YOLOv2 object detection application requires 4GB RAM to run smoothly.
# - Reduce the memory number (in MB) here if you physical machine does not have enough physical memory.
RAM = 4096

# Bento: Packer templates for building minimal Vagrant baseboxes
# The bento/ubuntu-XX.XX is a small image of about 500 MB, fast to download
BOX = "bento/ubuntu-20.04"
VM_NAME = "ubuntu-20.04-ndt"

# When using libvirt as the provider, use this box, bento boxes do not support libvirt.
BOX_LIBVIRT = "generic/ubuntu2004"

######################
#  Provision Script  #
######################

# Common bootstrap
$bootstrap= <<-SCRIPT
DEBIAN_FRONTEND=noninteractive apt-get update
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y

APT_PKGS=(
  ansible
  bash-completion
  dfc
  gdb
  git
  htop
  iperf
  iperf3
  make
  pkg-config
  python3
  python3-dev
  python3-pip
  sudo
  tmux
)
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "${APT_PKGS[@]}"
SCRIPT

$setup_x11_server= <<-SCRIPT
APT_PKGS=(
  openbox
  xauth
  xorg
  xterm
)
DEBIAN_FRONTEND=noninteractive apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y "${APT_PKGS[@]}"
SCRIPT

$setup_comnetsemu= <<-SCRIPT
# Apply a custom Xterm profile that looks better than the default.
cp /home/vagrant/comnetsemu/util/Xresources /home/vagrant/.Xresources
# xrdb can not run directly during vagrant up. Auto-works after reboot.
xrdb -merge /home/vagrant/.Xresources

cd /home/vagrant/comnetsemu/util || exit
bash ./install.sh -a

# Run the custom shell script, if it exists.
cd /home/vagrant/comnetsemu/util || exit
if [ -f "./vm_customize.sh" ]; then
  echo "*** Run VM customization script."
  bash ./vm_customize.sh
fi
SCRIPT

$post_installation= <<-SCRIPT
# Allow the vagrant user to use Docker without sudo.
usermod -aG docker vagrant
if [ -d /home/vagrant/.docker ]; then
  chown -R vagrant:vagrant /home/vagrant/.docker
fi
DEBIAN_FRONTEND=noninteractive apt-get autoclean -y
DEBIAN_FRONTEND=noninteractive apt-get autoremove -y
SCRIPT

$setup_libvirt_vm_always= <<-SCRIPT
# Configure the SSH server to allow X11 forwarding with sudo
# This is needed to use the Xterm feature of ComNetsEmu with libvirt/KVM
cp /home/vagrant/comnetsemu/util/sshd_config /etc/ssh/sshd_config
systemctl restart sshd.service
SCRIPT

####################
#  Vagrant Config  #
####################

Vagrant.configure("2") do |config|

  config.vm.define "NDT" do |ndt|
    ndt.vm.box = BOX
    # Sync ./ to home directory of vagrant to simplify the install script
    ndt.vm.synced_folder ".", "/vagrant", disabled: true
    ndt.vm.synced_folder ".", "/home/vagrant/comnetsemu"

    # For Virtualbox provider
    ndt.vm.provider "virtualbox" do |vb|
      vb.name = VM_NAME
      vb.cpus = CPUS
      vb.memory = RAM
      # MARK: The vCPUs should have SSE4 to compile DPDK applications.
      vb.customize ["setextradata", :id, "VBoxInternal/CPUM/SSE4.1", "1"]
      vb.customize ["setextradata", :id, "VBoxInternal/CPUM/SSE4.2", "1"]
    end

    # For libvirt provider
    ndt.vm.provider "libvirt" do |libvirt, override|
      # Overrides are used to modify default options that do not work for libvirt provider.
      override.vm.box = BOX_LIBVIRT
      override.vm.synced_folder ".", "/home/vagrant/comnetsemu", type: "nfs", nfs_version: 4

      libvirt.driver = "kvm"
      libvirt.cpus = CPUS
      libvirt.memory = RAM
    end

    ndt.vm.hostname = "NDT"
    ndt.vm.box_check_update = true
    ndt.vm.post_up_message = '
The VM is up! Run "$ vagrant ssh NDT" to ssh into the running VM.

If you are using an ARM processor, please create/edit the /boot/cmdline.txt file, and add:
cgroup_enable=cpuset cgroup_enable=memory cgroup_memory=1
    '

    ndt.vm.provision :shell, inline: $bootstrap, privileged: true
    ndt.vm.provision :shell, inline: $setup_x11_server, privileged: true
    ndt.vm.provision :shell, inline: $setup_comnetsemu, privileged: false
    ndt.vm.provision :shell, inline: $post_installation, privileged: true

    ndt.vm.provider "libvirt" do |libvirt, override|
      override.vm.provision :shell, inline: $setup_libvirt_vm_always, privileged: true, run: "always"
    end
    ndt.vm.provision :shell, privileged:false, run: "always", path: "./util/echo_banner.sh"

    # VM networking
    ndt.vm.network "forwarded_port", guest: 8888, host: 8888, host_ip: "127.0.0.1"
    ndt.vm.network "forwarded_port", guest: 8082, host: 8082
    ndt.vm.network "forwarded_port", guest: 8083, host: 8083
    ndt.vm.network "forwarded_port", guest: 8084, host: 8084
    ndt.vm.network "forwarded_port", guest: 8000, host: 8000
    ndt.vm.network "forwarded_port", guest: 3000, host: 1234
    ndt.vm.network "forwarded_port", guest: 8008, host: 8008, host_ip: "127.0.0.1"
    ndt.vm.network "forwarded_port", guest: 5000, host: 1235

    # - Uncomment the underlying line to add a private network to the VM.
    #   If VirtualBox is used as the hypervisor, this means adding or using (if already created) a host-only interface to the VM.
    ndt.vm.network "private_network", ip: "192.168.56.2"

    # Enable X11 forwarding
    ndt.ssh.forward_agent = true
    ndt.ssh.forward_x11 = true
  end
end
