#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ghost_protocol.py - Ghost Protocol
Ghost_Backup module - lightweight multi-threaded TCP port scanner

Purpose: scan TCP ports on localhost (or an authorized host) to verify
         firewall (e.g. ufw) allow/deny behavior.

WARNING: only scan hosts you own or have explicit permission to test.
"""

import json
import os
import argparse
import errno
import socket
import sys
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import logging

# Setup logging to both screen and file
logging.basicConfig(
    filename='ghost.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DualLogger:
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout
    def write(self, message):
        self.original_stdout.write(message)
        if message.strip():
            logging.info(message.strip())
    def isatty(self):
        return self.original_stdout.isatty()
    def flush(self):
        self.original_stdout.flush()

# Redirect stdout to capture prints
sys.stdout = DualLogger(sys.stdout)

# ---------------- Terminal colors ----------------
_TTY = sys.stdout.isatty()

class C:
    RED     = "\033[91m" if _TTY else ""
    GREEN   = "\033[92m" if _TTY else ""
    YELLOW  = "\033[93m" if _TTY else ""
    BLUE    = "\033[94m" if _TTY else ""
    MAGENTA = "\033[95m" if _TTY else ""
    CYAN    = "\033[96m" if _TTY else ""
    GRAY    = "\033[90m" if _TTY else ""
    BOLD    = "\033[1m"  if _TTY else ""
    RESET   = "\033[0m"  if _TTY else ""

# ---------------- Common service names ----------------
SERVICE_MAP = {
    20: "ftp-data", 21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp",
    53: "dns", 67: "dhcp", 69: "tftp", 80: "http", 110: "pop3",
    111: "rpcbind", 123: "ntp", 135: "msrpc", 137: "netbios",
    139: "netbios-ssn", 143: "imap", 161: "snmp", 389: "ldap",
    443: "https", 445: "smb", 465: "smtps", 587: "submission",
    636: "ldaps", 993: "imaps", 995: "pop3s", 1433: "mssql",
    1521: "oracle", 2049: "nfs", 2375: "docker", 2376: "docker-tls",
    3000: "node/grafana", 3306: "mysql", 3389: "rdp", 5432: "postgres",
    5900: "vnc", 6379: "redis", 8000: "http-alt", 8080: "http-proxy",
    8443: "https-alt", 8888: "http-alt", 9000: "php-fpm",
    9200: "elasticsearch", 11211: "memcached", 27017: "mongodb",
}

TOP_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445,
    993, 995, 1433, 1521, 3306, 3389, 5432, 5900, 6379, 8000,
    8080, 8443, 8888, 9000, 9200, 11211, 27017,
]

# ---------------- Helpers ----------------
def parse_ports(spec: str) -> list[int]:
    """Parse '22,80,8000-8010' style port expressions."""
    ports = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            a, b = int(a), int(b)
            if a > b:
                a, b = b, a
            ports.update(range(a, b + 1))
        else:
            ports.add(int(part))
    return sorted(p for p in ports if 1 <= p <= 65535)


def grab_banner(sock: socket.socket, port: int) -> str | None:
    """Best-effort banner grab. Returns None if nothing usable."""
    try:
        sock.settimeout(0.8)
        if port in (80, 8000, 8080, 8888):
            sock.sendall(b"HEAD / HTTP/1.0\r\nHost: localhost\r\n\r\n")
        elif port in (443, 8443):
            return None  # TLS handshake is out of scope
        data = sock.recv(1024)
        if not data:
            return None
        text = data.decode("utf-8", "replace").strip()
        first_line = text.splitlines()[0] if text else ""
        return first_line[:80] or None
    except Exception:
        return None


def scan_port(host: str, port: int, timeout: float, want_banner: bool):
    """
    Return (port, state, banner)
    state: 'open' | 'closed' | 'filtered'
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        code = s.connect_ex((host, port))
        if code == 0:
            banner = grab_banner(s, port) if want_banner else None
            return port, "open", banner
        if code in (errno.ECONNREFUSED, 111):
            return port, "closed", None
        return port, "filtered", None
    except socket.timeout:
        return port, "filtered", None
    except ConnectionRefusedError:
        return port, "closed", None
    except OSError:
        return port, "filtered", None
    finally:
        s.close()


def check_ufw() -> None:
    """Try to read ufw status (may need root). Silently skip on failure."""
    print(f"\n{C.CYAN}-- ufw status --{C.RESET}")
    try:
        r = subprocess.run(
            ["ufw", "status", "verbose"],
            capture_output=True, text=True, timeout=5, errors="replace",
        )
        if r.returncode != 0:
            print(f"{C.YELLOW}  cannot read ufw status (try sudo){C.RESET}")
            return
        for line in r.stdout.strip().splitlines():
            print(f"  {C.GRAY}{line}{C.RESET}")
    except FileNotFoundError:
        print(f"{C.GRAY}  ufw not installed (or not a Linux box), skipping{C.RESET}")
    except Exception as e:
        print(f"{C.YELLOW}  error reading ufw: {e}{C.RESET}")


# ---------------- Main ----------------
def main() -> int:
    # --- Added: Read configuration file ---
    config = {}
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            print(f"Failed to read config.json: {e}, using default configuration.")
    # --------------------------------------
    parser = argparse.ArgumentParser(
        description="ghost_protocol.py - Ghost Protocol port scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="examples:\n"
               "  python3 ghost_protocol.py\n"
               "  python3 ghost_protocol.py -H 192.168.1.10 -p 22,80,443\n"
               "  python3 ghost_protocol.py -p 1-1024 -t 0.5 -j 500\n"
               "  python3 ghost_protocol.py --top --banner\n",
    )
    parser.add_argument("-H", "--host", default=config.get("host", "127.0.0.1"),
                        help="target host (default: 127.0.0.1)")
    parser.add_argument("-p", "--ports", default=config.get("ports","22,80"),
                        help="port list, e.g. 22,80 or 1-1024 (default: 22,80)")
    parser.add_argument("--top", action="store_true",
                        help="scan TOP common ports (overrides -p)")
    parser.add_argument("-t", "--timeout", type=float, default=config.get("timeout", 1.0),
                        help="per-port timeout in seconds (default: 1.0)")
    parser.add_argument("-j", "--jobs", type=int, default=config.get("jobs", 200),
                        help="concurrent workers (default: 200)")
    parser.add_argument("-b", "--banner", action="store_true",
                        help="attempt banner grabbing (slower)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="also show closed ports")
    parser.add_argument("--check-ufw", action="store_true",
                        help="try to dump ufw status after the scan")
    parser.add_argument("--save", metavar="FILE",
                        help="save results to a test report")
    args = par ser.parse_args()

    # ---- Resolve target ----
    try:
        target_ip = socket.gethostbyname(args.host)
    except socket.gaierror as e:
        print(f"{C.RED}x cannot resolve host {args.host}: {e}{C.RESET}")
        return 1

    # ---- Resolve ports ----
    if args.top:
        ports = sorted(set(TOP_PORTS))
    else:
        try:
            ports = parse_ports(args.ports)
        except ValueError:
            print(f"{C.RED}x bad port spec: {args.ports}{C.RESET}")
            return 1
    if not ports:
        print(f"{C.RED}x no valid ports{C.RESET}")
        return 1

    # ---- Header ----
    start_ts = time.time()
    print(f"{C.MAGENTA}{C.BOLD}")
    print("  +------------------------------------------+")
    print("  |      GHOST PROTOCOL  -  ghost_protocol   |")
    print("  +------------------------------------------+")
    print(C.RESET)
    print(f"  {C.BOLD}target {C.RESET}: {args.host}"
          + (f" ({target_ip})" if args.host != target_ip else ""))
    print(f"  {C.BOLD}ports  {C.RESET}: {len(ports)}"
          + ("  [TOP]" if args.top else ""))
    print(f"  {C.BOLD}jobs   {C.RESET}: {args.jobs}    "
          f"{C.BOLD}timeout{C.RESET}: {args.timeout}s"
          + (f"    {C.BOLD}banner{C.RESET}: on" if args.banner else ""))
    print(f"  {C.BOLD}time   {C.RESET}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  {'-' * 44}\n")
# ---- Concurrent scan ----
    results = []
    total = len(ports)
    done = 0
    show_progress = total > 200

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {
            pool.submit(scan_port, target_ip, p, args.timeout, args.banner): p
            for p in ports
        }
        for fut in as_completed(futures):
           results.append(fut.result())
            done += 1
            if show_progress and done % 500 == 0:
                pct = done * 100 // total
                print(f"  {C.GRAY}scanning... {done}/{total} ({pct}%){C.RESET}",
                      end="\r", flush=True)

    if show_progress:
        print(" " * 45, end="\r")  # clear the progress line

    # ---- Sort and print results ----
    results.sort(key=lambda x: x[0])
    counts = {"open": 0, "closed": 0, "filtered": 0}
    lines = []

    for port, state, banner in results:
        counts[state] += 1
        svc = SERVICE_MAP.get(port, "unknown")

        if state == "open":
            line = f"  {C.GREEN}[OPEN    ]{C.RESET} {port:>5}/tcp  {svc:<14}"
            if banner:
                line += f"  {C.GRAY}>> {banner}{C.RESET}"
            print(line)
            lines.append(f"[OPEN    ] {port:>5}/tcp  {svc:<14} {banner or ''}".rstrip())
        elif state == "filtered":
            line = (f"  {C.YELLOW}[FILTERED]{C.RESET} {port:>5}/tcp  {svc:<14}  "
                    f"{C.GRAY}(dropped by firewall / timeout){C.RESET}")
            print(line)
            lines.append(f"[FILTERED] {port:>5}/tcp  {svc:<14}")
        elif args.verbose:
            line = f"  {C.GRAY}[CLOSED  ] {port:>5}/tcp  {svc:<14}{C.RESET}"
            print(line)
            lines.append(f"[CLOSED  ] {port:>5}/tcp  {svc:<14}")

    # ---- Summary ----
    elapsed = time.time() - start_ts
    print(f"\n  {'-' * 44}")
    print(f"  {C.BOLD}scan finished{C.RESET}  elapsed {elapsed:.2f}s")
    print(f"    {C.GREEN}open     : {counts['open']}{C.RESET}")
    print(f"    {C.YELLOW}filtered : {counts['filtered']}{C.RESET}")
    print(f"    {C.GRAY}closed   : {counts['closed']}{C.RESET}")

    if counts["open"] == 0:
        print(f"\n  {C.YELLOW}!  no open ports found. If you scanned loopback "
              f"from the same host, ufw usually allows loopback traffic -- "
              f"scan from another machine against the public IP to see the "
              f"real firewall rules.{C.RESET}")

    # ---- Optional ufw dump ----
    if args.check_ufw:
        check_ufw()

    # ---- Save report ----
    if args.save:
        try:
            with open(args.save, "w", encoding="utf-8") as f:
                f.write("# ghost_protocol scan report\n")
                f.write(f"# target: {args.host} ({target_ip})\n")
                f.write(f"# time  : {datetime.now().isoformat(timespec='seconds')}\n")
                f.write(f"# ports : {len(ports)}  open={counts['open']}  "
                        f"filtered={counts['filtered']}  closed={counts['closed']}\n\n")
                f.write("\n".join(lines) + "\n")
            print(f"\n  {C.CYAN}+ report saved to {args.save}{C.RESET}")
        except OSError as e:
            print(f"\n  {C.RED}x save failed: {e}{C.RESET}")

    print()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}x interrupted{C.RESET}")
        sys.exit(130)