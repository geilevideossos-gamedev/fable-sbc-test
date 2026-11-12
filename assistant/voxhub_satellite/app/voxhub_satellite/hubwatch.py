from __future__ import annotations

import argparse
import contextlib
import ipaddress
import json
import logging
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from pathlib import Path

from .launch import read_env_file

_LOGGER = logging.getLogger(__name__)

TABLE = "voxhub"
STATUS_FILE = Path("/run/voxhub/hub.json")

Runner = Callable[[Sequence[str], str], None]
Resolver = Callable[[str], list[str]]
Prober = Callable[[str], bool]


def ruleset(api_port: int = 6053, peripheral_port: int = 6055) -> str:
    return "\n".join(
        [
            f"table inet {TABLE} {{",
            "  set hub4 { type ipv4_addr; }",
            "  chain input {",
            "    type filter hook input priority filter; policy accept;",
            f"    tcp dport {api_port} ip saddr @hub4 accept",
            f"    tcp dport {api_port} drop",
            f'    tcp dport {peripheral_port} iifname != "lo" drop',
            "  }",
            "}",
            "",
        ]
    )


def run_nft(argv: Sequence[str], stdin: str = "") -> None:
    result = subprocess.run(
        ["nft", *argv], input=stdin, capture_output=True, text=True, timeout=15, check=False
    )
    if result.returncode != 0:
        raise RuntimeError(f"nft {' '.join(argv)} failed: {result.stderr.strip()}")


def install_firewall(runner: Runner = run_nft, api_port: int = 6053, peripheral_port: int = 6055) -> None:
    with contextlib.suppress(RuntimeError):
        runner(["delete", "table", "inet", TABLE], "")
    runner(["-f", "-"], ruleset(api_port, peripheral_port))


def set_hub_addresses(addresses: Sequence[str], runner: Runner = run_nft) -> None:
    runner(["flush", "set", "inet", TABLE, "hub4"], "")
    if addresses:
        runner(["add", "element", "inet", TABLE, "hub4", "{ " + ", ".join(addresses) + " }"], "")


def resolve(host: str) -> list[str]:
    try:
        return [str(ipaddress.IPv4Address(host))]
    except ValueError:
        pass
    infos = socket.getaddrinfo(host, None, socket.AF_INET, socket.SOCK_STREAM)
    return sorted({info[4][0] for info in infos})


def probe(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return 200 <= response.status < 500
    except urllib.error.HTTPError as err:
        return err.code < 500
    except (urllib.error.URLError, OSError, ValueError):
        return False


class HubWatch:
    def __init__(
        self,
        host: str,
        http_port: int = 8123,
        firewall: bool = True,
        runner: Runner = run_nft,
        resolver: Resolver = resolve,
        prober: Prober = probe,
        status_file: Path | None = STATUS_FILE,
    ) -> None:
        self.host = host
        self.http_port = http_port
        self.firewall = firewall
        self.runner = runner
        self.resolver = resolver
        self.prober = prober
        self.status_file = status_file
        self.addresses: list[str] = []
        self.reachable: bool | None = None

    def start(self) -> None:
        if self.firewall:
            install_firewall(self.runner)
            _LOGGER.info("Firewall: port 6053 only accepts connections from the hub %s", self.host)

    def step(self) -> None:
        try:
            addresses = self.resolver(self.host)
        except OSError as err:
            addresses = []
            _LOGGER.warning("Cannot resolve the hub %s: %s", self.host, err)
        if addresses and addresses != self.addresses:
            _LOGGER.info("Hub %s is at %s", self.host, ", ".join(addresses))
            self.addresses = addresses
            if self.firewall:
                set_hub_addresses(addresses, self.runner)
        target = self.addresses[0] if self.addresses else self.host
        reachable = self.prober(f"http://{target}:{self.http_port}/manifest.json")
        if reachable != self.reachable:
            if reachable:
                _LOGGER.info("Home Assistant answers at http://%s:%d", target, self.http_port)
            else:
                _LOGGER.warning(
                    "Home Assistant does not answer at http://%s:%d - answers from the hub cannot be played",
                    target,
                    self.http_port,
                )
            self.reachable = reachable
        if self.status_file is not None:
            try:
                self.status_file.parent.mkdir(parents=True, exist_ok=True)
                self.status_file.write_text(
                    json.dumps({"hub": self.host, "addresses": self.addresses, "reachable": reachable}) + "\n"
                )
            except OSError as err:
                _LOGGER.debug("Cannot write %s: %s", self.status_file, err)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="voxhub-hubwatch")
    parser.add_argument("--env-file", default="/etc/voxhub/satellite.env")
    parser.add_argument("--interval", type=float, default=60.0)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    values = read_env_file(Path(args.env_file))
    host = values.get("VOXHUB_HUB", "").strip()
    if not host:
        _LOGGER.error("VOXHUB_HUB is not set in %s", args.env_file)
        return 2
    watch = HubWatch(
        host,
        int(values.get("VOXHUB_HUB_PORT") or 8123),
        values.get("VOXHUB_FIREWALL", "1").strip().lower() not in ("0", "false", "no", "off"),
    )
    watch.start()
    while True:
        watch.step()
        if args.once:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
