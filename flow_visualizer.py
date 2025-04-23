import pygame
import requests
import time
import math
import hashlib

WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
VPN_COLOR = (0, 255, 255)

NODES = {
    'h1': (200, 450),
    'h2': (600, 450),
    'h3': (200, 150),
    'h4': (600, 150),
    's1': (400, 300),
}

MAC_TO_NODE = {
    "00:00:00:00:00:01": "h1",
    "00:00:00:00:00:02": "h2",
    "00:00:00:00:00:03": "h3",
    "00:00:00:00:00:04": "h4",
}

IP_LABELS = {
    "h1": "10.0.1.1 / 192.168.2.1",
    "h2": "10.0.1.2 / 192.168.2.2",
    "h3": "10.0.1.3",
    "h4": "10.0.1.4"
}

active_paths = {}


def get_color_for_pair(src, dst):
    key = f"{src}-{dst}"
    h = hashlib.md5(key.encode()).hexdigest()
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    return (r % 200 + 50, g % 200 + 50, b % 200 + 50)


def draw_arrow(screen, start, end, color):
    pygame.draw.line(screen, color, start, end, 3)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    arrow_size = 10
    dx1 = arrow_size * math.cos(angle - math.pi / 6)
    dy1 = arrow_size * math.sin(angle - math.pi / 6)
    dx2 = arrow_size * math.cos(angle + math.pi / 6)
    dy2 = arrow_size * math.sin(angle + math.pi / 6)
    pygame.draw.line(screen, color, end, (end[0] - dx1, end[1] - dy1), 3)
    pygame.draw.line(screen, color, end, (end[0] - dx2, end[1] - dy2), 3)


def draw_pulse(screen, path, t, color):
    if len(path) < 2:
        return

    total_segments = len(path) - 1
    segment = int(t * total_segments)
    segment_t = (t * total_segments) - segment

    if segment >= total_segments:
        segment = total_segments - 1
        segment_t = 1

    start = path[segment]
    end = path[segment + 1]
    x = int(start[0] + segment_t * (end[0] - start[0]))
    y = int(start[1] + segment_t * (end[1] - start[1]))
    pygame.draw.circle(screen, color, (x, y), 6)


def fetch_flows():
    try:
        r = requests.get("http://localhost:8080/stats/flow/1")
        data = r.json().get("1", [])
        return data
    except:
        return []


def draw_nodes(screen):
    for node, pos in NODES.items():
        pygame.draw.circle(screen, BLACK, pos, 30)
        label = font.render(node, True, WHITE)
        screen.blit(label, (pos[0] - label.get_width() // 2, pos[1] - 10))
        if node in IP_LABELS:
            ip_label = small_font.render(IP_LABELS[node], True, BLACK)
            screen.blit(ip_label, (pos[0] - ip_label.get_width() // 2, pos[1] - 50))


def main():
    pygame.init()
    global font, small_font
    font = pygame.font.SysFont("Arial", 18)
    small_font = pygame.font.SysFont("Arial", 14)
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Live SDN Flow Visualizer")

    pulse_phase = 0
    clock = pygame.time.Clock()

    while True:
        screen.fill(WHITE)
        draw_nodes(screen)
        flows = fetch_flows()

        current_paths = {}

        for flow in flows:
            match = flow.get("match", {})
            src_mac = match.get("dl_src")
            dst_mac = match.get("dl_dst")
            ip_src = match.get("ipv4_src", "")
            ip_dst = match.get("ipv4_dst", "")
            src_node = MAC_TO_NODE.get(src_mac)
            dst_node = MAC_TO_NODE.get(dst_mac)

            if src_node and dst_node:
                via = NODES["s1"]
                start = NODES[src_node]
                end = NODES[dst_node]

                is_vpn = ip_src.startswith("192.168.2.") or ip_dst.startswith("192.168.2.")
                color = VPN_COLOR if is_vpn else get_color_for_pair(src_node, dst_node)

                draw_arrow(screen, start, via, color)
                draw_arrow(screen, via, end, color)

                path_key = tuple(sorted([src_node, dst_node]))
                current_paths[path_key] = (start, via, end, color)

        for (src, dst), (start, via, end, color) in current_paths.items():
            draw_pulse(screen, [start, via, end], pulse_phase, color)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        pulse_phase += 0.01
        if pulse_phase > 1.0:
            pulse_phase = 0

        clock.tick(60)


if __name__ == '__main__':
    main()
