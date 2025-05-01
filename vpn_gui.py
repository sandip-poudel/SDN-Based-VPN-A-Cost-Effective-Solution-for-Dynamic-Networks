import pygame
import sys
import subprocess
import threading
import time
import requests
import collections

# Constants
H1_PID = "27143"
H2_PID = "27145"
WIDTH, HEIGHT = 1000, 600

# Colors
WHITE = (255, 255, 255)
GRAY = (180, 180, 180)
GREEN = (0, 255, 0)
BLUE = (100, 100, 255)
ORANGE = (255, 165, 0)
BLACK = (0, 0, 0)
PANEL_BG = (230, 230, 230)
PACKET_RADIUS = 6

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SDN-Controlled WireGuard VPN (Mininet + Ryu)")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 20)

wg_status = {f"h{i}": "Loading..." for i in range(1, 6)}
flow_display = []
flow_logs = collections.deque(maxlen=10)
side_tab_open = True

# side buttons
buttons = {
    "h1_to_h2": {"rect": pygame.Rect(WIDTH - 290, 400, 170, 30), "active": False},
    "h2_to_h1": {"rect": pygame.Rect(WIDTH - 290, 440, 170, 30), "active": False},
    "h3_to_h4": {"rect": pygame.Rect(WIDTH - 290, 480, 170, 30), "active": False},
    "h4_to_h3": {"rect": pygame.Rect(WIDTH - 290, 520, 170, 30), "active": False},
    "nonvpn_h5_to_h1": {"rect": pygame.Rect(WIDTH - 290, 560, 170, 30), "active": False},
    "allow_vpn_only": {"rect": pygame.Rect(WIDTH - 290, 100, 170, 30), "active": False},
    "allow_icmp_only": {"rect": pygame.Rect(WIDTH - 290, 140, 170, 30), "active": False},
    "allow_nonvpn": {"rect": pygame.Rect(WIDTH - 290, 180, 170, 30), "active": False}
}

port_map = {
    "h1_to_h2": (1, 2),
    "h2_to_h1": (2, 1),
    "h3_to_h4": (3, 4),
    "h4_to_h3": (4, 3),
    "nonvpn_h5_to_h1": (5, 1)
}

def log_flow_action(message):
    print(message)
    flow_logs.appendleft(message)

def send_flow_request(add, in_port, out_port):
    url = f"http://localhost:8080/stats/flowentry/{'add' if add else 'delete'}"
    payload = {"dpid": 1, "priority": 100, "match": {"in_port": in_port}}
    if add:
        payload["actions"] = [{"type": "OUTPUT", "port": out_port}]
    try:
        r = requests.post(url, json=payload, timeout=2)
        if r.status_code == 200:
            log_flow_action(f"{'Installed' if add else 'Removed'} flow: in_port={in_port} → out_port={out_port}")
            return True
    except Exception as e:
        log_flow_action(f"Error: {e}")
    return False

def fetch_ryu_flows():
    try:
        resp = requests.get("http://localhost:8080/stats/flow/1", timeout=1)
        flow_data = resp.json().get("1", [])
        return [
            f"in:{f.get('match', {}).get('in_port','?')} → out:{f.get('actions', [])} pkts:{f.get('packet_count', 0)} bytes:{f.get('byte_count', 0)}"
            for f in flow_data
        ]
    except Exception as e:
        return [f"Error: {e}"]

def toggle_side_tab():
    global side_tab_open
    side_tab_open = not side_tab_open

class Node:
    def __init__(self, x, y, label, color):
        self.pos = pygame.Vector2(x, y)
        self.radius = 25
        self.color = color
        self.label = label

    def draw(self, surface, status_text=""):
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)
        text = font.render(self.label, True, BLACK)
        surface.blit(text, text.get_rect(center=(int(self.pos.x), int(self.pos.y))))
        if status_text:
            for i, line in enumerate(status_text.split("\n")):
                rendered = font.render(line, True, BLACK)
                surface.blit(rendered, (int(self.pos.x - 30), int(self.pos.y + 30 + i * 15)))

    def is_hovered(self, pos):
        return self.pos.distance_to(pos) < self.radius

class Link:
    def __init__(self, node1, node2, vpn=False):
        self.node1 = node1
        self.node2 = node2
        self.vpn = vpn

    def draw(self, surface):
        color = GREEN if self.vpn else GRAY
        pygame.draw.line(surface, color, (int(self.node1.pos.x), int(self.node1.pos.y)), (int(self.node2.pos.x), int(self.node2.pos.y)), 4)

class Packet:
    def __init__(self, path, color=GRAY, speed=0.02):
        self.path = path
        self.segment = 0
        self.t = 0.0
        self.speed = speed
        self.color = color
        self.active = True

    def update(self):
        if not self.active or self.segment >= len(self.path) - 1:
            self.active = False
            return
        self.t += self.speed
        if self.t >= 1.0:
            self.segment += 1
            self.t = 0.0
            if self.segment >= len(self.path) - 1:
                self.active = False

    def draw(self, surface):
        if not self.active: return
        start, end = self.path[self.segment].pos, self.path[self.segment + 1].pos
        pos = start.lerp(end, self.t)
        pygame.draw.circle(surface, self.color, (int(pos.x), int(pos.y)), PACKET_RADIUS)

# Node positions
h1 = Node(100, 150, "h1", BLUE)
h2 = Node(500, 150, "h2", BLUE)
h3 = Node(100, 350, "h3", BLUE)
h4 = Node(500, 350, "h4", BLUE)
h5 = Node(300, 500, "h5", (255, 0, 0))  # non-VPN host
s1 = Node(300, 250, "s1", ORANGE)
nodes = [h1, h2, h3, h4, h5, s1]

def update_wg_status():
    while True:
        for h in ["h1", "h2"]:
            try:
                pid = H1_PID if h == "h1" else H2_PID
                out = subprocess.run(["sudo", "mnexec", "-a", pid, "wg"], capture_output=True, text=True)
                lines = out.stdout.splitlines()
                tx = hs = "N/A"
                for l in lines:
                    if "transfer" in l: tx = l.split(":", 1)[1].strip()
                    if "latest handshake" in l: hs = l.split(":", 1)[1].strip()
                wg_status[h] = f"HS: {hs}\nTX: {tx}"
            except:
                wg_status[h] = "Error"
        time.sleep(2)

threading.Thread(target=update_wg_status, daemon=True).start()

packets = []
spawn_timer = 0
last_flow_refresh = 0
running = True
selected_node = None

while running:
    screen.fill(WHITE)
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            toggle_side_tab()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            for node in nodes:
                if node.is_hovered(pos): selected_node = node
            for key, btn in buttons.items():
                if btn["rect"].collidepoint(pos):
                    btn["active"] = not btn["active"]
                    if key in port_map:
                        in_port, out_port = port_map[key]
                        if send_flow_request(btn["active"], in_port, out_port):
                            btn["active"] = btn["active"]
                    elif key == "allow_vpn_only":
                        flow = {"dpid": 1, "priority": 200, "match": {"eth_type": 2048, "ipv4_src": "10.10.0.0/24"}, "actions": [{"type": "OUTPUT", "port": "NORMAL"}]}
                        requests.post(f"http://localhost:8080/stats/flowentry/{'add' if btn['active'] else 'delete'}", json=flow)
                        log_flow_action(f"{'Installed' if btn['active'] else 'Removed'} VPN subnet rule")
                    elif key == "allow_icmp_only":
                        flow = {"dpid": 1, "priority": 200, "match": {"eth_type": 2048, "ip_proto": 1}, "actions": [{"type": "OUTPUT", "port": "NORMAL"}]}
                        requests.post(f"http://localhost:8080/stats/flowentry/{'add' if btn['active'] else 'delete'}", json=flow)
                        log_flow_action(f"{'Installed' if btn['active'] else 'Removed'} ICMP-only rule")
                    elif key == "allow_nonvpn":
                        flow = {"dpid": 1, "priority": 200, "match": {"eth_type": 2048, "ipv4_src": "192.168.0.0/16"}, "actions": [{"type": "OUTPUT", "port": "NORMAL"}]}
                        requests.post(f"http://localhost:8080/stats/flowentry/{'add' if btn['active'] else 'delete'}", json=flow)
                        log_flow_action(f"{'Installed' if btn['active'] else 'Removed'} non-VPN rule")

        elif event.type == pygame.MOUSEBUTTONUP: selected_node = None
        elif event.type == pygame.MOUSEMOTION and selected_node:
            selected_node.pos.update(event.pos)

    for key, (src, dst) in {
        "h1_to_h2": (h1, h2), "h2_to_h1": (h2, h1),
        "h3_to_h4": (h3, h4), "h4_to_h3": (h4, h3),
        "nonvpn_h5_to_h1": (h5, h1)
    }.items():
        if buttons[key]["active"]:
            Link(src, s1, True).draw(screen)
            Link(s1, dst, True).draw(screen)

    for node in nodes:
        node.draw(screen, wg_status.get(node.label, ""))

    spawn_timer += 1
    if spawn_timer >= 60:
        for key, (src, dst) in {
            "h1_to_h2": (h1, h2), "h2_to_h1": (h2, h1),
            "h3_to_h4": (h3, h4), "h4_to_h3": (h4, h3),
            "nonvpn_h5_to_h1": (h5, h1)
        }.items():
            if buttons[key]["active"]:
                packets.append(Packet([src, s1, dst], GREEN))
        spawn_timer = 0

    for p in packets:
        p.update()
        p.draw(screen)
    packets = [p for p in packets if p.active]

    if pygame.time.get_ticks() - last_flow_refresh > 3000:
        flow_display = fetch_ryu_flows()
        last_flow_refresh = pygame.time.get_ticks()

    if side_tab_open:
        panel_x = WIDTH - 300
        pygame.draw.rect(screen, PANEL_BG, (panel_x, 0, 300, HEIGHT))
        screen.blit(font.render("Ryu Flow Table", True, BLACK), (panel_x + 10, 10))
        for i, line in enumerate(flow_display[:20]):
            screen.blit(font.render(line, True, BLACK), (panel_x + 10, 30 + i * 18))
        screen.blit(font.render("SDN Flow Controls", True, BLACK), (panel_x + 10, 370))
        for key, btn in buttons.items():
            color = (0, 200, 0) if btn["active"] else (200, 0, 0)
            pygame.draw.rect(screen, color, btn["rect"])
            label = "Remove" if btn["active"] else "Add"
            screen.blit(font.render(f"{label} {key.replace('_', '→')}", True, WHITE), (btn["rect"].x + 10, btn["rect"].y + 6))
        screen.blit(font.render("Flow Action Log:", True, BLACK), (panel_x + 10, 560))
        for i, log in enumerate(flow_logs):
            screen.blit(font.render(log, True, BLACK), (panel_x + 10, 580 + i * 15))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
