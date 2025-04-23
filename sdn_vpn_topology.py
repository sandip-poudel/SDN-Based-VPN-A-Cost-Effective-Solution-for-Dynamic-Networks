#!/usr/bin/python3

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel

class SDNVPNTopo(Topo):
    def build(self):
        s1 = self.addSwitch('s1')
        h1 = self.addHost('h1', ip='10.0.1.1/24')
        h2 = self.addHost('h2', ip='10.0.1.2/24')
        h3 = self.addHost('h3', ip='10.0.1.3/24')
        h4 = self.addHost('h4', ip='10.0.1.4/24')
        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s1)
        self.addLink(h4, s1)

def run():
    topo = SDNVPNTopo()
    net = Mininet(
        topo=topo,
        controller=None,
        switch=OVSSwitch,
        autoSetMacs=True,
        autoStaticArp=True
    )

    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6633)
    net.start()

    s1 = net.get('s1')
    s1.cmd("ovs-vsctl set bridge s1 protocols=OpenFlow13")
    s1.cmd("ovs-vsctl set-fail-mode s1 secure")

    h1, h2, h3, h4 = net.get('h1'), net.get('h2'), net.get('h3'), net.get('h4')

    # WireGuard between h1 and h2
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

    print("[+] Configuring h2 WireGuard...")
    h2.cmd("ip link add wg0 type wireguard")
    h2.cmd("ip addr add 192.168.2.2/24 dev wg0")
    h2.cmd("wg set wg0 private-key /tmp/h2_priv")
    h2.cmd(f"wg set wg0 listen-port 51821")
    h2.cmd(f"wg set wg0 peer {h1_pub} endpoint 10.0.1.1:51820 allowed-ips 192.168.2.1/32 persistent-keepalive 15")
    h2.cmd("ip link set wg0 up")
    h2.cmd("ip route add 192.168.2.1/32 dev wg0")

    print("[*] Triggering WireGuard handshake with UDP...")
    h1.cmd("nc -u -z -w 1 10.0.1.2 51821")
    h2.cmd("nc -u -z -w 1 10.0.1.1 51820")

    print("\n[*] Ping tests:")
    print(h1.cmd("ping -c 2 192.168.2.2"))  # VPN ping
    print(h3.cmd("ping -c 2 10.0.1.4"))     # LAN ping

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
