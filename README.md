# Environment Setup for Mininet + WireGuard Flow Visualizer

---

## 1. Create Ubuntu VM in VirtualBox

1. **Download Ubuntu ISO**\
   Recommended: [Ubuntu 22.04 LTS](https://ubuntu.com/download/desktop)

2. **Create a new VM in VirtualBox**

   - Type: Linux
   - Version: Ubuntu (64-bit)
   - RAM: 2048 MB or more
   - Disk: 20 GB (dynamically allocated)

3. **Install Ubuntu** using the mounted ISO.

   - Choose any username and password.

---

## 2. Enable Bidirectional Copy & Paste (Optional)

1. In the running VM window, go to:\
   **Devices > Insert Guest Additions CD image…**

2. If prompted, click **Run**. If not, run manually:

   ```bash
   cd /media/$USER/VBox_GAs_*
   sudo ./VBoxLinuxAdditions.run
   ```

3. Reboot:

   ```bash
   sudo reboot
   ```

4. Enable clipboard and drag-drop in the VM window:

   - **Devices > Shared Clipboard > Bidirectional**
   - **Devices > Drag and Drop > Bidirectional**

---

## 3. Grant Sudo Access (Optional)

If your user gets `not in the sudoers file`, fix it like this:

```bash
# Login as root
su

# Add your user to sudo group
usermod -aG sudo yourusername

# Exit root shell and reboot
exit
reboot
```

---

## 4. System Update

```bash
sudo apt update && sudo apt upgrade -y
```

---

## 5. Install Dependencies

```bash
sudo apt install git openvswitch-switch net-tools python3-pip -y
```

---

## 6. Install Mininet

Clone the official Mininet repo and run the installer:

```bash
git clone https://github.com/mininet/mininet
cd mininet
sudo ./util/install.sh -a
```

---

## 7. Install Ryu and Required Python Packages

```bash
sudo apt install python3-ryu -y
pip3 install pygame requests
```

You can also install Ryu manually from source if needed:

```bash
git clone https://github.com/faucetsdn/ryu.git
cd ryu
pip3 install .
```

Verify Ryu:

```bash
ryu-manager --version
```

---

## 8. Clone the Flow Visualizer Project

```bash
cd ~
git clone https://github.com/your-username/flow-visualizer-sdn.git
cd flow-visualizer-sdn
```

Make sure the directory includes:

- `sdn_vpn_topology.py`
- `flow_visualizer.py`

---

## 9. Running the Network + Visualizer

### Step 1: Start the Ryu Controller with API

```bash
ryu-manager ryu.app.ofctl_rest ryu.app.simple_switch_13
```

### Step 2: In another terminal, run the topology

```bash
sudo python3 sdn_vpn_topology.py
```

This sets up:

- A switch (`s1`) and 4 hosts (`h1` to `h4`)
- WireGuard interfaces for VPN connections
- Ping test from `h1` to `h2` (VPN)
- Ping test from `h2` to `h4` (Non-VPN)

### Additional Mininet Commands to Try

```bash
# Inside the Mininet CLI
h1 ping -c 2 h2      # VPN traffic (sends 2 packets)
h1 ping -c 2 h4      # Non-VPN traffic (uses default interface)
h3 ping -c 2 h4      # Normal LAN traffic
h2 ping -c 2 h3      # Cross-traffic (non-VPN)
```

> **Note:** In this lab, **only h1 and h2 are configured with WireGuard** interfaces using the `192.168.2.x` subnet.
>
> - When you ping from `h1` to `h2`, it uses the `wg0` VPN tunnel — this is VPN traffic.
> - All other communications (like `h1 → h4`, `h3 → h4`, or `h2 → h3`) use their default 10.0.1.x interfaces and are **non-VPN**.
> - You can confirm this by running `ip a` and `wg show` inside Mininet to see which interfaces and IPs are in use. which are routed through the WireGuard interface. Any ping from h1 to h2 will use the VPN tunnel if properly configured. Traffic between other nodes (like h1 to h4 or h3 to h4) defaults to standard routing over their 10.0.x.x IPs and does not use WireGuard.

````

### Step 3: In a third terminal, run the visualizer
```bash
python3 flow_visualizer.py
````

The Pygame window will:

- Display each host and switch with their IPs
- Visualize flow paths using curved arrows
- Animate packet flow direction with colored pulses

---

## 10. Exit

- To exit Mininet:

```bash
exit
```

- To close Ryu: `CTRL+C`
- To close the visualizer: Close the Pygame window