# SDN-Based VPN – Full Setup Guide

---

## 1. Create Ubuntu VM in VirtualBox

### Requirements
- **Ubuntu 22.04 LTS** (recommended)
- **RAM**: 2048 MB or more
- **Disk**: 20 GB minimum

### Steps
1. **Download Ubuntu ISO**: [Ubuntu 22.04 LTS](https://ubuntu.com/download/desktop)
2. **Create VirtualBox VM**:
   - Type: Linux
   - Version: Ubuntu (64-bit)
   - Memory: 2 GB+
   - Disk: 20 GB (dynamically allocated)
3. **Install Ubuntu** using the ISO.

### Optional (Recommended)
- **Enable Shared Clipboard / Drag & Drop**:
  - Devices > Shared Clipboard > Bidirectional
  - Devices > Drag and Drop > Bidirectional

To enable clipboard support:

```bash
cd /media/$USER/VBox_GAs_*
sudo ./VBoxLinuxAdditions.run
sudo reboot
```

### Grant sudo access (if needed):
```bash
su
usermod -aG sudo yourusername
exit
sudo reboot
```

---

## 2. Install Dependencies

Update your packages and install required tools:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install git openvswitch-switch python3-pip wireguard net-tools -y
```

---

## 3. Install Mininet

```bash
git clone https://github.com/mininet/mininet
cd mininet
sudo ./util/install.sh -a
```

---

## 4. Install Ryu Controller

```bash
sudo apt install python3-ryu -y
```

Test it with:

```bash
ryu-manager --version
```

---

## 5. Install Pygame

```bash
pip3 install pygame
```

---

## 6. Generating WireGuard Keys

Each VPN-enabled host needs a **private key** and the peer's **public key**.

Generate keys like this:

```bash
wg genkey | tee h1_private.key | wg pubkey > h1_public.key
cat h1_private.key
cat h1_public.key
```

Do the same for h2:
```bash
wg genkey | tee h2_private.key | wg pubkey > h2_public.key
cat h2_private.key
cat h2_public.key
```


- Store them and update the topology file (`vpn_topology.py`) to reflect your values:
```python
priv_key='YOUR_PRIVATE_KEY'
peer_pub_key='YOUR_PEER_PUBLIC_KEY'
```

---

## 7. Cloning and Running the Application

```bash
git clone https://github.com/sandip-poudel/SDN-Based-VPN-A-Cost-Effective-Solution-for-Dynamic-Networks.git
cd SDN-Based # just press tab here and it should automatically fill it out for you
```

Ensure the following files are present:
- `vpn_gui.py`
- `vpn_topology.py`

### Start the system (3 terminals recommended):

**Terminal 1 – Ryu Controller**
```bash
ryu-manager ryu.app.simple_switch_13 ryu.app.ofctl_rest
```

**Terminal 2 – Start Mininet Topology**
```bash
sudo python3 vpn_topology.py
```

**Terminal 3 – Start GUI Application**
```bash
sudo python3 vpn_gui.py
```

---

## Notes

- You may need to modify PIDs (`H1_PID`, `H2_PID`) in `vpn_gui.py` if they differ.
- If a teammate wants to run the app, they must:
  - Generate their own VPN keys
  - Adjust `vpn_topology.py` with those keys
  - Adjust GUI's PIDs after running Mininet

---

## Testing VPN Rules

You can use the GUI to toggle rules like:
- Only allowing `10.10.0.0/24` VPN subnet traffic
- Allowing only ICMP packets
- Testing flows from a non-VPN host (h5 with 192.168.0.x)

These aren't fully implemented so they don't really work as they should.

---
