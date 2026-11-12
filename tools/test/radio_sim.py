import argparse
import binascii
import json
import os
import socket
import struct
import sys
import time

FLASH_SIZE = 0x58000
PAGE = 8192
BL_CONFIG = 0x57FD8
IMAGE_VALID_CONF = 0x57FEC
ICEPICK_DEVICE_ID = 0x50001318
FCFG_USER_ID = 0x50001294
PRCM_RAMHWOPT = 0x40082250
FLASH_SIZE_REG = 0x4003002C
MISC_CONF_1 = 0x500010A0
IEEE_PRIMARY = 0x500012F0


def read_hex(path):
    from intelhex import IntelHex

    return bytes(IntelHex(path).tobinarray())


class Chip:
    def __init__(self, gpio_dir, images, initial, bootloader_closed, log):
        self.gpio_dir = gpio_dir
        self.images = images
        self.bootloader_closed = bootloader_closed
        self.log = log
        self.flash = bytearray(b"\xff" * FLASH_SIZE)
        if initial in images:
            data = images[initial]
            self.flash[: len(data)] = data
        self.mode = "off"
        self.last_reset = self.gpio(24)
        self.last_boot_pin = self.gpio(25)
        self.pressed_at = None
        self.events = []
        self.boot()

    def gpio(self, line):
        try:
            with open(os.path.join(self.gpio_dir, "gpio%d" % line)) as handle:
                return handle.read().strip()
        except OSError:
            return "0" if line == 24 else "1"

    def image_valid(self):
        return struct.unpack_from("<I", self.flash, IMAGE_VALID_CONF)[0] == 0

    def backdoor(self):
        config = struct.unpack_from("<I", self.flash, BL_CONFIG)[0]
        return (config >> 24) == 0xC5 and (config & 0xFF) == 0xC5 and ((config >> 8) & 0xFF) == 15 and not (config >> 16) & 1

    def identify(self):
        for name, data in self.images.items():
            if bytes(self.flash[: len(data)]) == data and all(b == 0xFF for b in self.flash[len(data):]):
                return name
        return "unknown"

    def boot(self):
        if self.gpio(24) == "1":
            self.mode = "reset"
        elif not self.image_valid():
            self.mode = "bootloader"
        elif self.gpio(25) == "0" and self.backdoor() and not self.bootloader_closed:
            self.mode = "bootloader"
        else:
            self.mode = "firmware:" + self.identify()
        self.log("boot -> %s" % self.mode)

    def poll(self):
        level = self.gpio(24)
        if level != self.last_reset:
            self.last_reset = level
            self.boot()
        pin = self.gpio(25)
        if pin != self.last_boot_pin:
            self.last_boot_pin = pin
            if self.mode == "firmware:router" and pin == "0":
                self.pressed_at = time.monotonic()
            elif self.mode == "firmware:router" and pin == "1" and self.pressed_at is not None:
                if time.monotonic() - self.pressed_at >= 0.05:
                    self.events.append("router-button")
                    self.log("router button click: leave and rejoin")
                self.pressed_at = None


class Session:
    def __init__(self, chip, conn):
        self.chip = chip
        self.conn = conn
        self.buffer = bytearray()
        self.synced = False
        self.status = 0x40
        self.download = None

    def send(self, data):
        try:
            self.conn.sendall(bytes(data))
        except OSError:
            pass

    def feed(self, data):
        mode = self.chip.mode
        if mode == "bootloader":
            self.buffer += data
            self.bootloader()
        elif mode == "firmware:coordinator":
            self.buffer += data
            self.znp()
        elif mode == "firmware:thread":
            self.buffer += data
            self.spinel()
        else:
            self.buffer.clear()

    def bootloader(self):
        while True:
            if not self.synced:
                index = self.buffer.find(b"\x55\x55")
                if index < 0:
                    del self.buffer[:-1]
                    return
                del self.buffer[: index + 2]
                self.synced = True
                self.send(b"\x00\xcc")
                continue
            while self.buffer and self.buffer[0] in (0x00, 0xCC, 0x33):
                if len(self.buffer) >= 2 and self.buffer[0] == 0x00 and self.buffer[1] in (0xCC, 0x33):
                    del self.buffer[:2]
                    continue
                if self.buffer[0] == 0x00 and len(self.buffer) < 2:
                    return
                break
            if len(self.buffer) < 2:
                return
            size = self.buffer[0]
            if size < 3 or len(self.buffer) < size:
                if size < 3:
                    del self.buffer[:1]
                    continue
                return
            packet = bytes(self.buffer[:size])
            del self.buffer[:size]
            body = packet[2:]
            if sum(body) & 0xFF != packet[1]:
                self.send(b"\x00\x33")
                continue
            self.command(body[0], body[1:])

    def reply(self, payload):
        self.send(bytes([len(payload) + 2, sum(payload) & 0xFF]) + bytes(payload))

    def command(self, cmd, data):
        flash = self.chip.flash
        self.send(b"\x00\xcc")
        if cmd == 0x23:
            self.reply([self.status])
            return
        self.status = 0x40
        if cmd == 0x20:
            return
        if cmd == 0x28:
            self.reply([0x00, 0x00, 0x30, 0x82])
        elif cmd == 0x2A:
            address = struct.unpack(">I", data[:4])[0]
            values = {
                ICEPICK_DEVICE_ID: [0x2F, 0x70, 0xB7, 0x3B],
                FCFG_USER_ID: [0x00, 0x40, 0x00, 0x00],
                FLASH_SIZE_REG: [FLASH_SIZE // PAGE, 0, 0, 0],
                PRCM_RAMHWOPT: [3, 0, 0, 0],
                MISC_CONF_1: [0x01, 0, 0, 0],
                IEEE_PRIMARY: [0x11, 0x22, 0x33, 0x44],
                IEEE_PRIMARY + 4: [0x55, 0x66, 0x77, 0x88],
            }
            if address < FLASH_SIZE:
                self.reply(list(flash[address : address + 4]))
            else:
                self.reply(values.get(address, [0, 0, 0, 0]))
        elif cmd == 0x2C:
            flash[:] = b"\xff" * FLASH_SIZE
            self.chip.events.append("bank-erase")
        elif cmd == 0x26:
            address = struct.unpack(">I", data[:4])[0]
            start = address - address % PAGE
            flash[start : start + PAGE] = b"\xff" * PAGE
            self.chip.events.append("sector-erase")
        elif cmd == 0x21:
            address, size = struct.unpack(">II", data[:8])
            if address + size > FLASH_SIZE:
                self.status = 0x43
            else:
                self.download = [address, size]
        elif cmd == 0x24:
            if not self.download:
                self.status = 0x42
                return
            address, remaining = self.download
            chunk = data[:remaining]
            for offset, value in enumerate(chunk):
                flash[address + offset] &= value
            self.download = [address + len(chunk), remaining - len(chunk)]
            self.chip.events.append("write")
        elif cmd == 0x27:
            address, size = struct.unpack(">II", data[:8])
            crc = binascii.crc32(bytes(flash[address : address + size])) & 0xFFFFFFFF
            self.reply(list(struct.pack(">I", crc)))
        elif cmd == 0x25:
            self.chip.events.append("reset-command")
            self.chip.boot()
            self.synced = False
        else:
            self.status = 0x41

    def znp(self):
        while True:
            start = self.buffer.find(b"\xfe")
            if start < 0:
                self.buffer.clear()
                return
            del self.buffer[:start]
            if len(self.buffer) < 5 or len(self.buffer) < self.buffer[1] + 5:
                return
            length = self.buffer[1]
            frame = bytes(self.buffer[1 : length + 5])
            del self.buffer[: length + 5]
            command0, command1 = frame[1], frame[2]
            if command0 == 0x21 and command1 == 0x01:
                self.znp_send(0x61, 0x01, bytes([0x79, 0x07]))
            elif command0 == 0x21 and command1 == 0x02:
                self.znp_send(0x61, 0x02, bytes([2, 1, 2, 7, 1]) + struct.pack("<I", 20250321) + b"\x00")

    def znp_send(self, command0, command1, data):
        body = bytes([len(data), command0, command1]) + data
        checksum = 0
        for value in body:
            checksum ^= value
        self.send(b"\xfe" + body + bytes([checksum]))

    def spinel(self):
        if self.buffer.count(0x7E) >= 2:
            self.buffer.clear()
            payload = bytes([0x81, 0x06, 0x02]) + b"SL-OPENTHREAD/Koenkk-2025.3.1; CC1352P2\x00"
            self.send(hdlc(payload))


def hdlc_crc(data):
    crc = 0xFFFF
    for value in data:
        crc ^= value
        for _ in range(8):
            crc = (crc >> 1) ^ 0x8408 if crc & 1 else crc >> 1
    return crc ^ 0xFFFF


def hdlc(payload):
    crc = hdlc_crc(payload)
    out = bytearray([0x7E])
    for value in payload + bytes([crc & 0xFF, crc >> 8]):
        if value in (0x7E, 0x7D, 0x11, 0x13, 0xF8):
            out += bytes([0x7D, value ^ 0x20])
        else:
            out.append(value)
    out.append(0x7E)
    return bytes(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gpio-dir", required=True)
    parser.add_argument("--port-file", required=True)
    parser.add_argument("--image", action="append", default=[])
    parser.add_argument("--initial", default="blank")
    parser.add_argument("--bootloader-closed", action="store_true")
    parser.add_argument("--state-file")
    args = parser.parse_args()
    images = {}
    for item in args.image:
        name, _, path = item.partition("=")
        images[name] = read_hex(path)
    os.makedirs(args.gpio_dir, exist_ok=True)
    for line, value in ((24, "0"), (25, "1")):
        path = os.path.join(args.gpio_dir, "gpio%d" % line)
        if not os.path.exists(path):
            with open(path, "w") as handle:
                handle.write(value + "\n")

    def log(message):
        print("[radio-sim] " + message, file=sys.stderr, flush=True)

    chip = Chip(args.gpio_dir, images, args.initial, args.bootloader_closed, log)
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(4)
    server.setblocking(False)
    with open(args.port_file, "w") as handle:
        handle.write("socket://127.0.0.1:%d\n" % server.getsockname()[1])

    def save_state(previous):
        state = {"mode": chip.mode, "events": len(chip.events)}
        if args.state_file and state != previous:
            with open(args.state_file + ".part", "w") as handle:
                json.dump({"mode": chip.mode, "firmware": chip.identify(), "events": chip.events}, handle)
            os.replace(args.state_file + ".part", args.state_file)
        return state

    sessions = []
    running = True
    last_state = None
    while running:
        chip.poll()
        try:
            conn, _ = server.accept()
            conn.setblocking(False)
            sessions.append(Session(chip, conn))
        except BlockingIOError:
            pass
        except OSError:
            running = False
        busy = False
        for session in list(sessions):
            try:
                data = session.conn.recv(4096)
                if not data:
                    session.conn.close()
                    sessions.remove(session)
                    continue
                busy = True
                session.feed(data)
            except BlockingIOError:
                pass
            except OSError:
                sessions.remove(session)
        last_state = save_state(last_state)
        if not busy:
            time.sleep(0.0005)


if __name__ == "__main__":
    main()
