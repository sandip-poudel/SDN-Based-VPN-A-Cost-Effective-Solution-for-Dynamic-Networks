#!/usr/bin/python3

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel

class SDNVPNTopo(Topo):
    def build(self):
        s1 = self.addSwitch('s1')
        h1 = self.addHost('h1', ip='10.0.1.1/24')
        h2 = self.addHost('h2', ip='10.0.1.2/24')
        self.addLink(h1, s1)
        self.addLink(h2, s1)

def run():
    topo = SDNVPNTopo()
    net = Mininet(topo=topo, controller=None, switch=OVSSwitch)
    net.start()

    s1 = net.get('s1')
    s1.cmd("ovs-vsctl set Bridge s1 fail_mode=standalone")
    s1.cmd("ovs-vsctl set-controller s1 none")

    h1, h2 = net.get('h1'), net.get('h2')
    h1.cmd("sysctl -w net.ipv4.ip_forward=1")
    h2.cmd("sysctl -w net.ipv4.ip_forward=1")

    print("[+] Generating WireGuard keys...")
    h1.cmd("wg genkey | tee /tmp/h1_priv | wg pubkey > /tmp/h1_pub")
    h2.cmd("wg genkey | tee /tmp/h2_priv | wg pubkey > /tmp/h2_pub")
    h1_pub = h1.cmd("cat /tmp/h1_pub").strip()
    h2_pub = h2.cmd("cat /tmp/h2_pub").strip()

    print("[+] Configuring h1 WireGuard...")
    h1.cmd("ip link add wg0 type wireguard")
    h1.cmd("ip addr add 192.168.2.1/24 dev wg0")
    h1.cmd("wg set wg0 private-key /tmp/h1_priv")
    h1.cmd(f"wg set wg0 listen-port 51820")
    h1.cmd(f"wg set wg0 peer {h2_pub} endpoint 10.0.1.2:51821 allowed-ips 192.168.2.2/32 persistent-keepalive 15")
    h1.cmd("ip link set wg0 up")
    h1.cmd("ip route add 192.168.2.2/32 dev wg0")
    h1.cmd("ip route add 10.0.1.2 dev h1-eth0")

    print("[+] Configuring h2 WireGuard...")
    h2.cmd("ip link add wg0 type wireguard")
    h2.cmd("ip addr add 192.168.2.2/24 dev wg0")
    h2.cmd("wg set wg0 private-key /tmp/h2_priv")
    h2.cmd(f"wg set wg0 listen-port 51821")
    h2.cmd(f"wg set wg0 peer {h1_pub} endpoint 10.0.1.1:51820 allowed-ips 192.168.2.1/32 persistent-keepalive 15")
    h2.cmd("ip link set wg0 up")
    h2.cmd("ip route add 192.168.2.1/32 dev wg0")
    h2.cmd("ip route add 10.0.1.1 dev h2-eth0")

    print("[*] Triggering WireGuard handshake with UDP...")
    h1.cmd("nc -u -z -w 1 10.0.1.2 51821")
    h2.cmd("nc -u -z -w 1 10.0.1.1 51820")

    print("\n=== h1 WireGuard Status ===")
    print(h1.cmd("wg show"))
    print("=== h1 IP Info ===")
    print(h1.cmd("ip a"))
    print("=== h1 Routes ===")
    print(h1.cmd("ip route"))

    print("\n=== h2 WireGuard Status ===")
    print(h2.cmd("wg show"))
    print("=== h2 IP Info ===")
    print(h2.cmd("ip a"))
    print("=== h2 Routes ===")
    print(h2.cmd("ip route"))

    print("\n[*] Testing ping from h1 to h2 over VPN:")
    print(h1.cmd("ping -c 4 192.168.2.2"))

    print("\n If '0 received' above, run 'h1 wg show' and 'h2 wg show' inside CLI to check for handshake.")
    print(" You can try re-triggering handshake with:")
    print("    h1 nc -u -z -w 1 10.0.1.2 51821")
    print("    h2 nc -u -z -w 1 10.0.1.1 51820")

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
