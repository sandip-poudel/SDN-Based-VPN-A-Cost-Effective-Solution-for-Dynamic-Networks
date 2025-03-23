# Environment Setup for Mininet + WireGuard Lab


---

## 1. Create Ubuntu VM in VirtualBox

1. **Download Ubuntu ISO**  
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

1. In the running VM window, go to:  
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
sudo apt install git openvswitch-switch -y
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

## 7. Install Ryu

```bash
sudo apt install python3-ryu -y
```

- You can verify the installation by running :

```bash
ryu-manager --version
```

## Your setup should now be complete.


## Cloning the Repository and Running the Python Script

Follow these steps to clone your project repository and test the WireGuard-over-Mininet setup.

### 1. Navigate to your workspace directory
```bash
cd ~
```

### 2. Clone the repository
Replace the URL with your actual GitHub repo:
```bash
git clone https://github.com/sandip-poudel/SDN-Based-VPN-A-Cost-Effective-Solution-for-Dynamic-Networks.git
cd SDN-Based-VPN-A-Cost-Effective-Solution-for-Dynamic-Networks
```

### 3. (Optional) Verify the contents
```bash
ls
```
You should see the Python script, e.g., `sdn_vpn_topology.py`.

### 4. Run the topology setup script with `sudo`
```bash
sudo python3 sdn_vpn_topology.py
```

This script will:
- Set up a Mininet topology with 2 hosts and 1 switch
- Generate WireGuard key pairs on both hosts
- Configure WireGuard interfaces
- Add public keys and allowed IPs
- Bring up the interfaces and test connectivity

The script should try running a ping test and log the results immediately in the terminal.
If it drops any packets then something probably went wrong.
Otherwise if it successfully receives 4 packets, then you are good to go.

### 5. Exit Mininet
To stop the Mininet simulation:
```bash
exit
```


