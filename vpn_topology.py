#!/usr/bin/python3

from mininet.net import Mininet
from mininet.node import RemoteController, Host
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.cli import CLI
from mininet.log import setLogLevel
import os

class VPNHost(Host):
    def config(self, **params):
        super().config(**params)

        priv_key = self.params['priv_key']
        peer_pub_key = self.params['peer_pub_key']
        peer_ip = self.params['peer_ip']
        local_ip = "10.10.0." + self.IP().split('.')[-1]

        print(f"[{self.name}] local_ip={local_ip}, peer_ip={peer_ip}")

        config = f"""
[Interface]
PrivateKey = {priv_key}
Address = {local_ip}/24
ListenPort = 51820

[Peer]
PublicKey = {peer_pub_key}
AllowedIPs = 10.10.0.0/24
Endpoint = {peer_ip}:51820
PersistentKeepalive = 25
""".strip()

        path = f"/tmp/{self.name}"
        os.makedirs(path, exist_ok=True)
        with open(f"{path}/wg0.conf", "w") as f:
            f.write(config)

        self.cmd("ip link add wg0 type wireguard")
        self.cmd(f"wg setconf wg0 {path}/wg0.conf")
        self.cmd(f"ip addr add {local_ip}/24 dev wg0")
        self.cmd("ip link set wg0 up")
        self.cmd("ip route add 10.10.0.0/24 dev wg0")
        self.cmd(f"echo '[{self.name}] WireGuard fully configured'")
        self.cmd("wg show")

class VPNTopo(Topo):
    def build(self):
        s1 = self.addSwitch("s1")

        # change keys as necessary
        
        h1 = self.addHost("h1", cls=VPNHost,
            priv_key="MBpoBlmpDOA3StykbOFmFLCnDS5lR0wuxpscJRFjAko=",
            peer_pub_key="NBlSPBPMyV7H0mZjSNW+hCW+fk5LmwcFAIn/Yghc90c=",
            peer_ip="10.0.0.2")

        h2 = self.addHost("h2", cls=VPNHost,
            priv_key="0GXQLXXmrjI+dCpjkkFEtBl2gaucN0MrdUTzm1waWFM=",
            peer_pub_key="eR6mfHspAb5FidTxmbGK7m9NIbvHzlxKwGlijyLWM0o=",
            peer_ip="10.0.0.1")

        h3 = self.addHost("h3")
        h4 = self.addHost("h4")
        h5 = self.addHost("h5")  # non-VPN host

        for h in [h1, h2, h3, h4, h5]:
            self.addLink(h, s1)

def run():
    topo = VPNTopo()
    net = Mininet(topo=topo, controller=RemoteController, link=TCLink)
    net.start()

    h3, h4, h5 = net.get("h3"), net.get("h4"), net.get("h5")

    h3.cmd("ip addr add 10.10.0.3/24 dev h3-eth0")
    h4.cmd("ip addr add 10.10.0.4/24 dev h4-eth0")
    h5.cmd("ip addr add 192.168.1.5/24 dev h5-eth0")

    for host in [h3, h4, h5]:
        host.cmd(f"ip link set {host.name}-eth0 up")

    CLI(net)
    net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    run()
