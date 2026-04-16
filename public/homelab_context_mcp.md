# HOMELAB INFRASTRUCTURE CONTEXT
> Generated on Wed Apr 15 11:49:56 PM EDT 2026 from host: pve
> This document adheres to MCP-friendly semantic structure for AI context analysis.

## System: Host Node
```yaml
Hostname: pve
Kernel: 6.17.13-2-pve
PVE Version: pve-manager/9.1.6/71482d1833ded40a (running kernel: 6.17.13-2-pve)
CPU Model: AMD Ryzen 7 3700X 8-Core Processor
```

---
## Resource: Network
- **ID:** host-net
- **Name:** Interfaces
- **Description:** Physical and Virtual Bridges configuration
- **Source:** /etc/network/interfaces

```config
auto lo
iface lo inet loopback

iface enp42s0 inet manual

iface nic1 inet manual

# On garde le pont physique, mais on enlève l'IP ici
auto vmbr0
iface vmbr0 inet manual
	bridge-ports enp42s0
	bridge-stp off
	bridge-fd 0
	bridge-vlan-aware yes
        bridge-vids 10 30 40 99
        bridge-igmp-snooping off

# On crée l'interface de gestion spécifique au VLAN 10 (Trusted)
auto vmbr0.10
iface vmbr0.10 inet static
	address 192.168.10.2/24
	gateway 192.168.10.1

auto vmbr1
iface vmbr1 inet manual
	bridge-ports nic1
	bridge-stp off
	bridge-fd 0
	bridge-vlan-aware yes
#WAN-Modem

source /etc/network/interfaces.d/*

```

---
## Resource: Storage
- **ID:** pve-storage
- **Name:** Storage Config
- **Description:** ZFS Pools, NFS, and Local Storage definitions
- **Source:** /etc/pve/storage.cfg

```config
dir: local
	path /var/lib/vz
	content backup,iso,vztmpl,import

lvmthin: local-lvm
	thinpool data
	vgname pve
	content rootdir,images

zfspool: Data-Pool
	pool Data-Pool
	content rootdir,images
	mountpoint /Data-Pool
	nodes pve


```

## Inventory: LXC Containers
---
## Resource: LXC
- **ID:** 101
- **Name:** NAS
- **Description:** Linux Container Configuration
- **Source:** /etc/pve/lxc/101.conf

```config
arch: amd64
cores: 1
features: nesting=1,mknod=1
hostname: NAS
memory: 512
mp0: /Data-Pool/partage,mp=/mnt/data
net0: name=eth0,bridge=vmbr0,firewall=0,gw=192.168.10.1,hwaddr=BC:24:11:35:A9:18,ip=192.168.10.10/24,tag=10,type=veth
onboot: 1
ostype: debian
rootfs: Data-Pool:subvol-101-disk-0,size=8G
startup: order=2
swap: 512
lxc.apparmor.profile: unconfined

```

---
## Resource: LXC
- **ID:** 102
- **Name:** jellyfin-lxc
- **Description:** Linux Container Configuration
- **Source:** /etc/pve/lxc/102.conf

```config
# --- PASSTHROUGH GPU NVIDIA (RTX 5060Ti) ---
# --- MEDIAS ---
#lxc.mount.entry%3A /dev/nvidia-modeset dev/nvidia-modeset none bind,optional,create=file
arch: amd64
cores: 4
features: nesting=1,keyctl=1
hostname: jellyfin-lxc
memory: 4096
mp0: /Data-Pool/partage/medias/music,mp=/media/music
mp1: /Data-Pool/partage/streaming,mp=/media/streaming
nameserver: 192.168.1.200
net0: name=eth0,bridge=vmbr0,hwaddr=BC:24:11:F8:AB:67,ip=dhcp,type=veth
onboot: 0
ostype: debian
rootfs: Data-Pool:subvol-102-disk-0,size=16G
swap: 0
lxc.cgroup2.devices.allow: c 195:* rwm
lxc.cgroup2.devices.allow: c 511:* rwm
lxc.cgroup2.devices.allow: c 236:* rwm
lxc.mount.entry: /dev/nvidia0 dev/nvidia0 none bind,optional,create=file
lxc.mount.entry: /dev/nvidiactl dev/nvidiactl none bind,optional,create=file
lxc.mount.entry: /dev/nvidia-uvm dev/nvidia-uvm none bind,optional,create=file
lxc.mount.entry: /dev/nvidia-uvm-tools dev/nvidia-uvm-tools none bind,optional,create=file
lxc.mount.entry: /dev/nvidia-caps dev/nvidia-caps none bind,optional,create=dir

```

---
## Resource: LXC
- **ID:** 103
- **Name:** pve-scripts-local
- **Description:** Linux Container Configuration
- **Source:** /etc/pve/lxc/103.conf
- **Tags:** community-script;pve-scripts-local

```config
arch: amd64
cores: 2
features: nesting=1,keyctl=1
hostname: pve-scripts-local
memory: 4096
net0: name=eth0,bridge=vmbr0,hwaddr=BC:24:11:66:EA:85,ip=192.168.1.206/24,gw=192.168.1.200,type=veth
onboot: 1
ostype: debian
rootfs: local-lvm:vm-103-disk-0,size=8G
startup: order=2,up=60
swap: 512
tags: community-script;pve-scripts-local
timezone: America/Toronto
unprivileged: 1

```

---
## Resource: LXC
- **ID:** 105
- **Name:** nginxproxymanager
nginxproxymanager
nginxproxymanager
- **Description:** Linux Container Configuration
- **Source:** /etc/pve/lxc/105.conf
- **Tags:** community-script;proxy
community-script;proxy
community-script;proxy

```config
arch: amd64
cores: 2
features: keyctl=1,nesting=1
hostname: nginxproxymanager
memory: 2048
net0: name=eth0,bridge=vmbr0,hwaddr=BC:24:11:A6:93:7E,ip=192.168.1.201/24,gw=192.168.1.200,type=veth
onboot: 1
ostype: debian
parent: Pre_Kernel_Update
rootfs: local-lvm:vm-105-disk-0,size=8G
startup: order=2,up=60
swap: 512
tags: community-script;proxy
unprivileged: 1

[Pre_Kernel_Update]
#Pre_Kernel_Update
arch: amd64
cores: 2
features: keyctl=1,nesting=1
hostname: nginxproxymanager
memory: 2048
net0: name=eth0,bridge=vmbr0,hwaddr=BC:24:11:A6:93:7E,ip=192.168.1.201/24,gw=192.168.1.200,type=veth
onboot: 1
ostype: debian
parent: pre-lxc-stack-update
rootfs: local-lvm:vm-105-disk-0,size=8G
snaptime: 1773420819
startup: order=2,up=60
swap: 512
tags: community-script;proxy
unprivileged: 1

[pre-lxc-stack-update]
#Avant MAJ pve-container/lxc-pve
arch: amd64
cores: 2
features: keyctl=1,nesting=1
hostname: nginxproxymanager
memory: 2048
net0: name=eth0,bridge=vmbr0,hwaddr=BC:24:11:A6:93:7E,ip=192.168.1.201/24,gw=192.168.1.200,type=veth
onboot: 1
ostype: debian
rootfs: local-lvm:vm-105-disk-0,size=8G
snaptime: 1770573806
startup: order=2,up=60
swap: 512
tags: community-script;proxy
unprivileged: 1

```

---
## Resource: LXC
- **ID:** 106
- **Name:** ollama
- **Description:** Linux Container Configuration
- **Source:** /etc/pve/lxc/106.conf
- **Tags:** ai;community-script;nvidia

```config
#lxc.mount.entry%3A /dev/serial/by-id  dev/serial/by-id  none bind,optional,create=dir
#lxc.mount.entry%3A /dev/ttyUSB0       dev/ttyUSB0       none bind,optional,create=file
#lxc.mount.entry%3A /dev/ttyUSB1       dev/ttyUSB1       none bind,optional,create=file
#lxc.mount.entry%3A /dev/ttyACM0       dev/ttyACM0       none bind,optional,create=file
#lxc.mount.entry%3A /dev/ttyACM1       dev/ttyACM1       none bind,optional,create=file
#dev0%3A /dev/nvidia0,gid=44
#dev1%3A /dev/nvidiactl,gid=44
#dev2%3A /dev/nvidia-modeset,gid=44
#dev3%3A /dev/nvidia-uvm,gid=44
#dev4%3A /dev/nvidia-uvm-tools,gid=44
#dev5%3A /dev/nvidia-caps/nvidia-cap1,gid=44
#dev6%3A /dev/nvidia-caps/nvidia-cap2,gid=44
arch: amd64
cores: 6
features: nesting=1,mknod=1
hostname: ollama
memory: 12288
mp0: /mnt/ssd-models,mp=/models
net0: name=eth0,bridge=vmbr0,hwaddr=BC:24:11:85:6D:0D,ip=192.168.1.205/24,gw=192.168.1.200,type=veth
onboot: 1
ostype: ubuntu
rootfs: local-lvm:vm-106-disk-0,size=50G
swap: 4096
tags: ai;community-script;nvidia
lxc.cgroup2.devices.allow: c 195:* rwm
lxc.cgroup2.devices.allow: c 511:* rwm
lxc.cgroup2.devices.allow: c 236:* rwm
lxc.mount.entry: /dev/nvidia0 dev/nvidia0 none bind,optional,create=file
lxc.mount.entry: /dev/nvidiactl dev/nvidiactl none bind,optional,create=file
lxc.mount.entry: /dev/nvidia-uvm dev/nvidia-uvm none bind,optional,create=file
lxc.mount.entry: /dev/nvidia-modeset dev/nvidia-modeset none bind,optional,create=file
lxc.mount.entry: /dev/nvidia-uvm-tools dev/nvidia-uvm-tools none bind,optional,create=file
lxc.cgroup2.devices.allow: a
lxc.cap.drop: 
lxc.cgroup2.devices.allow: c 188:* rwm
lxc.cgroup2.devices.allow: c 189:* rwm
lxc.apparmor.profile: unconfined

```

---
## Resource: LXC
- **ID:** 107
- **Name:** openwebui
- **Description:** Linux Container Configuration
- **Source:** /etc/pve/lxc/107.conf
- **Tags:** ai;community-script;interface

```config
arch: amd64
cores: 2
features: keyctl=1,nesting=1
hostname: openwebui
memory: 8192
mp1: /Data-Pool/projets,mp=/src
net0: name=eth0,bridge=vmbr0,hwaddr=BC:24:11:85:AD:27,ip=192.168.1.207/24,gw=192.168.1.200,type=veth
onboot: 1
ostype: debian
rootfs: local-lvm:vm-107-disk-0,size=25G
startup: order=2,up=60
swap: 512
tags: ai;community-script;interface
unprivileged: 1

```

---
## Resource: LXC
- **ID:** 108
- **Name:** searxng
searxng
- **Description:** Linux Container Configuration
- **Source:** /etc/pve/lxc/108.conf
- **Tags:** community-script;search
community-script;search

```config
arch: amd64
cores: 2
features: keyctl=1,nesting=1
hostname: searxng
memory: 2048
nameserver: 1.1.1.1
net0: name=eth0,bridge=vmbr0,hwaddr=BC:24:11:BD:FA:2F,ip=192.168.1.202/24,gw=192.168.1.200,type=veth
onboot: 1
ostype: debian
parent: Pre_Kernel_Update
rootfs: local-lvm:vm-108-disk-0,size=7G
startup: order=2,up=60
swap: 512
tags: community-script;search
unprivileged: 1

[Pre_Kernel_Update]
#Pre_Kernel_Update
arch: amd64
cores: 2
features: keyctl=1,nesting=1
hostname: searxng
memory: 2048
nameserver: 1.1.1.1
net0: name=eth0,bridge=vmbr0,hwaddr=BC:24:11:BD:FA:2F,ip=192.168.1.202/24,gw=192.168.1.200,type=veth
onboot: 1
ostype: debian
rootfs: local-lvm:vm-108-disk-0,size=7G
snaptime: 1773421013
startup: order=2,up=60
swap: 512
tags: community-script;search
unprivileged: 1

```

---
## Resource: LXC
- **ID:** 109
- **Name:** qbittorrent
- **Description:** Linux Container Configuration
- **Source:** /etc/pve/lxc/109.conf
- **Tags:** community-script;torrent

```config
#<div align='center'>
#  <a href='https%3A//Helper-Scripts.com' target='_blank' rel='noopener noreferrer'>
#    <img src='https%3A//raw.githubusercontent.com/community-scripts/ProxmoxVE/main/misc/images/logo-81x112.png' alt='Logo' style='width%3A81px;height%3A112px;'/>
#  </a>
#
#  <h2 style='font-size%3A 24px; margin%3A 20px 0;'>qBittorrent LXC</h2>
#
#  <p style='margin%3A 16px 0;'>
#    <a href='https%3A//ko-fi.com/community_scripts' target='_blank' rel='noopener noreferrer'>
#      <img src='https%3A//img.shields.io/badge/&#x2615;-Buy us a coffee-blue' alt='spend Coffee' />
#    </a>
#  </p>
#
#  <span style='margin%3A 0 10px;'>
#    <i class="fa fa-github fa-fw" style="color%3A #f5f5f5;"></i>
#    <a href='https%3A//github.com/community-scripts/ProxmoxVE' target='_blank' rel='noopener noreferrer' style='text-decoration%3A none; color%3A #00617f;'>GitHub</a>
#  </span>
#  <span style='margin%3A 0 10px;'>
#    <i class="fa fa-comments fa-fw" style="color%3A #f5f5f5;"></i>
#    <a href='https%3A//github.com/community-scripts/ProxmoxVE/discussions' target='_blank' rel='noopener noreferrer' style='text-decoration%3A none; color%3A #00617f;'>Discussions</a>
#  </span>
#  <span style='margin%3A 0 10px;'>
#    <i class="fa fa-exclamation-circle fa-fw" style="color%3A #f5f5f5;"></i>
#    <a href='https%3A//github.com/community-scripts/ProxmoxVE/issues' target='_blank' rel='noopener noreferrer' style='text-decoration%3A none; color%3A #00617f;'>Issues</a>
#  </span>
#</div>
arch: amd64
cores: 2
features: nesting=1,keyctl=1
hostname: qbittorrent
memory: 2048
mp0: /Data-Pool/partage/downloads,mp=/downloads
nameserver: 1.1.1.1
net0: name=eth0,bridge=vmbr0,hwaddr=BC:24:11:50:BF:94,ip=dhcp,ip6=auto,type=veth
onboot: 0
ostype: debian
rootfs: local-lvm:vm-109-disk-0,size=8G
searchdomain: 1.1.1.1
startup: order=2,up=60
swap: 512
tags: community-script;torrent
timezone: America/Toronto
unprivileged: 1

```

---
## Resource: LXC
- **ID:** 110
- **Name:** prowlarr
- **Description:** Linux Container Configuration
- **Source:** /etc/pve/lxc/110.conf
- **Tags:** arr;community-script

```config
arch: amd64
cores: 2
features: nesting=1,keyctl=1
hostname: prowlarr
memory: 1024
mp0: /Data-Pool/partage/downloads,mp=/downloads
net0: name=eth0,bridge=vmbr0,hwaddr=BC:24:11:1E:F3:1B,ip=dhcp,ip6=auto,type=veth
onboot: 0
ostype: debian
rootfs: local-lvm:vm-110-disk-0,size=4G
startup: order=2,up=60
swap: 512
tags: arr;community-script
timezone: America/Toronto
unprivileged: 1

```

---
## Resource: LXC
- **ID:** 111
- **Name:** flaresolverr
- **Description:** Linux Container Configuration
- **Source:** /etc/pve/lxc/111.conf
- **Tags:** community-script;proxy

```config
#<div align='center'>
#  <a href='https%3A//Helper-Scripts.com' target='_blank' rel='noopener noreferrer'>
#    <img src='https%3A//raw.githubusercontent.com/community-scripts/ProxmoxVE/main/misc/images/logo-81x112.png' alt='Logo' style='width%3A81px;height%3A112px;'/>
#  </a>
#
#  <h2 style='font-size%3A 24px; margin%3A 20px 0;'>FlareSolverr LXC</h2>
#
#  <p style='margin%3A 16px 0;'>
#    <a href='https%3A//ko-fi.com/community_scripts' target='_blank' rel='noopener noreferrer'>
#      <img src='https%3A//img.shields.io/badge/&#x2615;-Buy us a coffee-blue' alt='spend Coffee' />
#    </a>
#  </p>
#
#  <span style='margin%3A 0 10px;'>
#    <i class="fa fa-github fa-fw" style="color%3A #f5f5f5;"></i>
#    <a href='https%3A//github.com/community-scripts/ProxmoxVE' target='_blank' rel='noopener noreferrer' style='text-decoration%3A none; color%3A #00617f;'>GitHub</a>
#  </span>
#  <span style='margin%3A 0 10px;'>
#    <i class="fa fa-comments fa-fw" style="color%3A #f5f5f5;"></i>
#    <a href='https%3A//github.com/community-scripts/ProxmoxVE/discussions' target='_blank' rel='noopener noreferrer' style='text-decoration%3A none; color%3A #00617f;'>Discussions</a>
#  </span>
#  <span style='margin%3A 0 10px;'>
#    <i class="fa fa-exclamation-circle fa-fw" style="color%3A #f5f5f5;"></i>
#    <a href='https%3A//github.com/community-scripts/ProxmoxVE/issues' target='_blank' rel='noopener noreferrer' style='text-decoration%3A none; color%3A #00617f;'>Issues</a>
#  </span>
#</div>
arch: amd64
cores: 2
features: nesting=1,keyctl=1
hostname: flaresolverr
memory: 2048
net0: name=eth0,bridge=vmbr0,hwaddr=BC:24:11:21:F8:83,ip=dhcp,ip6=auto,type=veth
onboot: 0
ostype: debian
rootfs: local-lvm:vm-111-disk-0,size=4G
startup: order=2,up=60
swap: 512
tags: community-script;proxy
timezone: America/Toronto
unprivileged: 1

```

---
## Resource: LXC
- **ID:** 112
- **Name:** lidarr
- **Description:** Linux Container Configuration
- **Source:** /etc/pve/lxc/112.conf
- **Tags:** arr;community-script;torrent;usenet

```config
arch: amd64
cores: 2
features: nesting=1,keyctl=1
hostname: lidarr
memory: 1024
mp0: /Data-Pool/partage/medias/music,mp=/music
mp1: /Data-Pool/partage/downloads,mp=/downloads
net0: name=eth0,bridge=vmbr0,hwaddr=BC:24:11:FD:5F:50,ip=dhcp,ip6=auto,type=veth
onboot: 0
ostype: debian
rootfs: local-lvm:vm-112-disk-0,size=4G
startup: order=2,up=60
swap: 512
tags: arr;community-script;torrent;usenet
timezone: America/Toronto
unprivileged: 1

```

---
## Resource: LXC
- **ID:** 113
- **Name:** comfyui
- **Description:** Linux Container Configuration
- **Source:** /etc/pve/lxc/113.conf
- **Tags:** ai;community-script

```config
arch: amd64
cores: 4
dev0: /dev/nvidia0,gid=44
dev1: /dev/nvidiactl,gid=44
dev2: /dev/nvidia-modeset,gid=44
dev3: /dev/nvidia-uvm,gid=44
dev4: /dev/nvidia-uvm-tools,gid=44
dev5: /dev/nvidia-caps/nvidia-cap1,gid=44
dev6: /dev/nvidia-caps/nvidia-cap2,gid=44
features: nesting=1,keyctl=1
hostname: comfyui
memory: 20480
mp0: /mnt/ssd-models/comfyui,mp=/opt/ComfyUI/models
mp1: /mnt/ssd-outputs/gallery,mp=/opt/ComfyUI/output
net0: name=eth0,bridge=vmbr0,hwaddr=BC:24:11:1D:A6:D3,ip=dhcp,type=veth
onboot: 0
ostype: debian
rootfs: local-lvm:vm-113-disk-0,size=25G
swap: 4096
tags: ai;community-script
timezone: America/Toronto
unprivileged: 1

```

---
## Resource: LXC
- **ID:** 114
- **Name:** piper-tts
- **Description:** Linux Container Configuration
- **Source:** /etc/pve/lxc/114.conf
- **Tags:** ai;tts

```config
arch: amd64
cores: 2
features: nesting=1,keyctl=1
hostname: piper-tts
memory: 1024
nameserver: 192.168.1.200
net0: name=eth0,bridge=vmbr0,gw=192.168.1.200,hwaddr=BC:24:11:40:2A:FB,ip=192.168.1.215/24,type=veth
onboot: 1
ostype: debian
rootfs: local-lvm:vm-114-disk-0,size=4G
startup: order=2,up=60
swap: 512
tags: ai;tts
timezone: America/Toronto
unprivileged: 1

```

---
## Resource: LXC
- **ID:** 115
- **Name:** ent-1101
- **Description:** Linux Container Configuration
- **Source:** /etc/pve/lxc/115.conf

```config
arch: amd64
cores: 1
features: nesting=1,keyctl=1
hostname: ent-1101
memory: 512
mp0: /Data-Pool/secrets,mp=/root/.secrets,ro=1
net0: name=eth0,bridge=vmbr0,gw=192.168.1.200,hwaddr=BC:24:11:62:B9:C3,ip=192.168.1.210/24,type=veth
onboot: 1
ostype: debian
rootfs: local-lvm:vm-115-disk-0,size=4G
swap: 512
unprivileged: 1

```

---
## Resource: LXC
- **ID:** 116
- **Name:** xtts-api
- **Description:** Linux Container Configuration
- **Source:** /etc/pve/lxc/116.conf
- **Tags:** ai;nvidia;tts

```config
arch: amd64
cores: 4
features: nesting=1,mknod=1
hostname: xtts-api
memory: 8192
nameserver: 192.168.1.200
net0: name=eth0,bridge=vmbr0,gw=192.168.1.200,hwaddr=BC:24:11:88:99:AA,ip=192.168.1.217/24,type=veth
ostype: debian
rootfs: local-lvm:vm-116-disk-0,size=40G
swap: 2048
tags: ai;nvidia;tts
timezone: America/Toronto
unprivileged: 1
lxc.cgroup2.devices.allow: c 195:* rwm
lxc.cgroup2.devices.allow: c 511:* rwm
lxc.cgroup2.devices.allow: c 236:* rwm
lxc.mount.entry: /dev/nvidia0 dev/nvidia0 none bind,optional,create=file
lxc.mount.entry: /dev/nvidiactl dev/nvidiactl none bind,optional,create=file
lxc.mount.entry: /dev/nvidia-uvm dev/nvidia-uvm none bind,optional,create=file
lxc.mount.entry: /dev/nvidia-modeset dev/nvidia-modeset none bind,optional,create=file
lxc.mount.entry: /dev/nvidia-uvm-tools dev/nvidia-uvm-tools none bind,optional,create=file
lxc.cgroup2.devices.allow: a
lxc.cap.drop: 
lxc.apparmor.profile: unconfined

```

## Inventory: Virtual Machines
---
## Resource: VM
- **ID:** 100
- **Name:** OPNsense
OPNsense
- **Description:** QEMU Virtual Machine Configuration
- **Source:** /etc/pve/qemu-server/100.conf

```config
agent: 1
boot: order=scsi0;ide2;net0
cores: 4
cpu: host
ide2: none,media=cdrom
memory: 8192
meta: creation-qemu=10.1.2,ctime=1767416140
name: OPNsense
net0: virtio=BC:24:11:BD:C2:FF,bridge=vmbr0,firewall=0
net1: virtio=BC:24:11:F5:E8:B6,bridge=vmbr1,firewall=0
numa: 0
onboot: 1
ostype: l26
parent: pre-lxc-stack-update
scsi0: local-lvm:vm-100-disk-0,iothread=1,size=32G
scsihw: virtio-scsi-single
smbios1: uuid=7dbef1b1-facc-4ebb-9235-d39413742104
sockets: 1
startup: order=1,up=30
vmgenid: 0b309b5e-9a7a-47c6-9851-1788bd978ae0

[pre-lxc-stack-update]
#Avant MAJ pve-container/lxc-pve
agent: 1
boot: order=scsi0;ide2;net0
cores: 4
cpu: host
ide2: none,media=cdrom
memory: 8192
meta: creation-qemu=10.1.2,ctime=1767416140
name: OPNsense
net0: virtio=BC:24:11:BD:C2:FF,bridge=vmbr0,firewall=0
net1: virtio=BC:24:11:F5:E8:B6,bridge=vmbr1,firewall=0
numa: 0
onboot: 1
ostype: l26
scsi0: local-lvm:vm-100-disk-0,iothread=1,size=32G
scsihw: virtio-scsi-single
smbios1: uuid=7dbef1b1-facc-4ebb-9235-d39413742104
snaptime: 1770573778
sockets: 1
startup: order=1,up=30
vmgenid: 0b309b5e-9a7a-47c6-9851-1788bd978ae0

```

