#!/usr/bin/env python3
"""Read-only STM32 ROM-UART probe and factory-flash backup helper.

The probe and backup subcommands intentionally implement no erase, write,
unprotect, option-byte, or go command.  They are suitable for preserving the
H60 factory image before an approved flash and for independent readback after
an approved flash.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterable, Optional, Protocol


ACK = 0x79
NACK = 0x1F
SYNC = 0x7F

CMD_GET = 0x00
CMD_GET_ID = 0x02
CMD_READ_MEMORY = 0x11

EXPECTED_CHIP_ID = 0x0413
FLASH_BASE = 0x08000000
FLASH_SIZE = 512 * 1024
FLASH_END = FLASH_BASE + FLASH_SIZE
READ_CHUNK = 256


class BootloaderError(RuntimeError):
    """A ROM-bootloader transaction or safety check failed."""


class Transport(Protocol):
    def write(self, data: bytes) -> int: ...

    def read(self, size: int) -> bytes: ...


def _xor_bytes(data: bytes) -> int:
    value = 0
    for byte in data:
        value ^= byte
    return value


class STM32Bootloader:
    """Minimal read-only subset of ST's AN3155 UART protocol."""

    def __init__(self, transport: Transport):
        self.transport = transport

    def _read_exact(self, size: int) -> bytes:
        result = bytearray()
        while len(result) < size:
            block = self.transport.read(size - len(result))
            if not block:
                raise BootloaderError(
                    f"serial timeout: wanted {size} bytes, received {len(result)}"
                )
            result.extend(block)
        return bytes(result)

    def _expect_ack(self, context: str) -> None:
        reply = self._read_exact(1)[0]
        if reply == NACK:
            raise BootloaderError(f"bootloader NACK during {context}")
        if reply != ACK:
            raise BootloaderError(
                f"unexpected byte 0x{reply:02X} during {context}; expected ACK"
            )

    def sync(self) -> None:
        self.transport.write(bytes((SYNC,)))
        self._expect_ack("sync")

    def _command(self, command: int, context: str) -> None:
        self.transport.write(bytes((command, command ^ 0xFF)))
        self._expect_ack(context)

    def get(self) -> tuple[int, tuple[int, ...]]:
        self._command(CMD_GET, "GET command")
        following_minus_one = self._read_exact(1)[0]
        response = self._read_exact(following_minus_one + 1)
        self._expect_ack("GET response")
        if not response:
            raise BootloaderError("GET returned an empty response")
        return response[0], tuple(response[1:])

    def get_id(self) -> tuple[int, bytes]:
        self._command(CMD_GET_ID, "GET ID command")
        id_length_minus_one = self._read_exact(1)[0]
        raw_id = self._read_exact(id_length_minus_one + 1)
        self._expect_ack("GET ID response")
        if len(raw_id) < 2:
            raise BootloaderError(f"GET ID returned only {len(raw_id)} byte(s)")
        return int.from_bytes(raw_id, "big"), raw_id

    def read_memory(self, address: int, size: int) -> bytes:
        if not (1 <= size <= READ_CHUNK):
            raise ValueError("ROM read size must be between 1 and 256 bytes")
        _validate_flash_range(address, size)

        self._command(CMD_READ_MEMORY, "READ MEMORY command")
        encoded_address = address.to_bytes(4, "big")
        self.transport.write(encoded_address + bytes((_xor_bytes(encoded_address),)))
        self._expect_ack("READ MEMORY address")

        encoded_size = size - 1
        self.transport.write(bytes((encoded_size, encoded_size ^ 0xFF)))
        self._expect_ack("READ MEMORY length")
        return self._read_exact(size)


def _validate_flash_range(address: int, size: int) -> None:
    if size <= 0:
        raise BootloaderError("flash read size must be positive")
    if address < FLASH_BASE or address + size > FLASH_END:
        raise BootloaderError(
            f"refusing read outside 0x{FLASH_BASE:08X}..0x{FLASH_END:08X}"
        )


def validate_factory_image(image: bytes) -> dict[str, object]:
    """Reject blank/truncated data and validate the Cortex-M vector pair."""

    if len(image) != FLASH_SIZE:
        raise BootloaderError(
            f"backup length is {len(image)} bytes; expected {FLASH_SIZE}"
        )
    if image == b"\xFF" * len(image):
        raise BootloaderError("backup is entirely 0xFF (blank or unreadable flash)")
    if image == b"\x00" * len(image):
        raise BootloaderError("backup is entirely 0x00 (invalid read)")

    initial_msp, reset_vector = struct.unpack_from("<II", image, 0)
    # A descending Cortex-M stack is normally initialized one byte past the
    # RAM region, so the exclusive upper address is a valid initial MSP.
    msp_in_sram = 0x20000000 <= initial_msp <= 0x20020000
    msp_in_ccm = 0x10000000 <= initial_msp <= 0x10010000
    if not (msp_in_sram or msp_in_ccm):
        raise BootloaderError(
            f"initial MSP 0x{initial_msp:08X} is outside STM32F407 RAM"
        )
    reset_address = reset_vector & ~1
    if not (reset_vector & 1):
        raise BootloaderError(
            f"reset vector 0x{reset_vector:08X} is not a Thumb address"
        )
    if not (FLASH_BASE <= reset_address < FLASH_END):
        raise BootloaderError(
            f"reset vector 0x{reset_vector:08X} is outside the 512 KiB flash"
        )

    return {
        "bytes": len(image),
        "sha256": hashlib.sha256(image).hexdigest(),
        "initial_msp": f"0x{initial_msp:08X}",
        "reset_vector": f"0x{reset_vector:08X}",
        "non_ff_bytes": sum(byte != 0xFF for byte in image),
        "non_zero_bytes": sum(byte != 0x00 for byte in image),
    }


@dataclass(frozen=True)
class AutoISPProfile:
    name: str
    invert_dtr: bool
    invert_rts: bool


AUTO_ISP_PROFILES = (
    # This was the successful mapping during the H60 read-only probe.
    AutoISPProfile("inverted-both", True, True),
    AutoISPProfile("direct", False, False),
    AutoISPProfile("inverted-dtr", True, False),
    AutoISPProfile("inverted-rts", False, True),
)


class SerialAdapter:
    def __init__(self, port: str, timeout: float):
        try:
            import serial  # type: ignore
        except ImportError as exc:
            raise BootloaderError(
                "pyserial is required for hardware access; run this script with "
                "the Codex bundled Python runtime"
            ) from exc

        try:
            self.serial = serial.Serial(
                port=port,
                baudrate=115200,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_EVEN,
                stopbits=serial.STOPBITS_ONE,
                timeout=timeout,
                write_timeout=timeout,
                exclusive=True,
            )
        except Exception as exc:
            raise BootloaderError(f"cannot open serial port {port}: {exc}") from exc

    def write(self, data: bytes) -> int:
        try:
            written = self.serial.write(data)
            self.serial.flush()
        except Exception as exc:
            raise BootloaderError(f"serial write failed: {exc}") from exc
        if written != len(data):
            raise BootloaderError(
                f"short serial write: wrote {written} of {len(data)} bytes"
            )
        return written

    def read(self, size: int) -> bytes:
        try:
            return bytes(self.serial.read(size))
        except Exception as exc:
            raise BootloaderError(f"serial read failed: {exc}") from exc

    def reset_buffers(self) -> None:
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()

    @staticmethod
    def _mapped_level(physical_high: bool, inverted: bool) -> bool:
        return not physical_high if inverted else physical_high

    def set_physical_lines(
        self, *, boot_high: bool, reset_released: bool, profile: AutoISPProfile
    ) -> None:
        self.serial.dtr = self._mapped_level(boot_high, profile.invert_dtr)
        self.serial.rts = self._mapped_level(reset_released, profile.invert_rts)

    def enter_bootloader(self, profile: AutoISPProfile) -> None:
        # Establish a known run state, hold BOOT high across a reset pulse, and
        # leave BOOT high for the complete read-only ROM session.
        self.set_physical_lines(
            boot_high=False, reset_released=True, profile=profile
        )
        time.sleep(0.05)
        self.set_physical_lines(
            boot_high=True, reset_released=True, profile=profile
        )
        time.sleep(0.02)
        self.set_physical_lines(
            boot_high=True, reset_released=False, profile=profile
        )
        time.sleep(0.08)
        self.set_physical_lines(
            boot_high=True, reset_released=True, profile=profile
        )
        time.sleep(0.18)
        self.reset_buffers()

    def restore_run_lines(self, profile: AutoISPProfile) -> None:
        self.set_physical_lines(
            boot_high=False, reset_released=True, profile=profile
        )

    def close(self) -> None:
        self.serial.close()


def connect_read_only(
    port: str, profile_name: str, timeout: float
) -> tuple[SerialAdapter, STM32Bootloader, AutoISPProfile]:
    adapter = SerialAdapter(port, timeout)
    if profile_name == "auto":
        profiles: Iterable[AutoISPProfile] = AUTO_ISP_PROFILES
    else:
        profiles = tuple(
            profile for profile in AUTO_ISP_PROFILES if profile.name == profile_name
        )
    last_error: Optional[Exception] = None
    try:
        for profile in profiles:
            try:
                adapter.enter_bootloader(profile)
                client = STM32Bootloader(adapter)
                client.sync()
                return adapter, client, profile
            except BootloaderError as exc:
                last_error = exc
        raise BootloaderError(
            f"ROM bootloader did not acknowledge any allowed auto-ISP profile: "
            f"{last_error}"
        )
    except Exception:
        adapter.close()
        raise


def inspect_bootloader(client: STM32Bootloader) -> dict[str, object]:
    chip_id, raw_id = client.get_id()
    if chip_id != EXPECTED_CHIP_ID:
        raise BootloaderError(
            f"unexpected chip ID 0x{chip_id:04X}; expected 0x{EXPECTED_CHIP_ID:04X}"
        )
    version, commands = client.get()
    if CMD_READ_MEMORY not in commands:
        raise BootloaderError("ROM bootloader does not advertise READ MEMORY")
    return {
        "chip_id": f"0x{chip_id:04X}",
        "raw_chip_id": raw_id.hex(),
        "bootloader_version": f"0x{version:02X}",
        "supported_commands": [f"0x{command:02X}" for command in commands],
    }


def read_factory_flash(
    client: STM32Bootloader, progress: Optional[BinaryIO] = None
) -> bytes:
    image = bytearray()
    for offset in range(0, FLASH_SIZE, READ_CHUNK):
        address = FLASH_BASE + offset
        last_error: Optional[Exception] = None
        for _attempt in range(3):
            try:
                block = client.read_memory(address, READ_CHUNK)
                image.extend(block)
                last_error = None
                break
            except BootloaderError as exc:
                last_error = exc
                time.sleep(0.05)
        if last_error is not None:
            raise BootloaderError(
                f"read failed at 0x{address:08X} after 3 attempts: {last_error}"
            )
        if progress is not None and (
            len(image) % (32 * 1024) == 0 or len(image) == FLASH_SIZE
        ):
            progress.write(
                f"read {len(image):6d}/{FLASH_SIZE} bytes "
                f"({100 * len(image) // FLASH_SIZE:3d}%)\n".encode()
            )
            progress.flush()
    return bytes(image)


def save_new_file(path: Path, data: bytes) -> None:
    """Save atomically without ever replacing an existing backup."""

    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise BootloaderError(f"refusing to overwrite existing file: {path}")

    partial = path.with_name(f".{path.name}.partial-{os.getpid()}")
    fd = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(partial, path)
        except FileExistsError as exc:
            raise BootloaderError(f"refusing to overwrite existing file: {path}") from exc
        partial.unlink()
    except Exception:
        # Keep a partial file for diagnosis; never present it as a valid backup.
        raise


def _emit(record: dict[str, object]) -> None:
    print(json.dumps(record, indent=2, sort_keys=True))


def _run_hardware(args: argparse.Namespace) -> int:
    adapter, client, profile = connect_read_only(
        args.port, args.auto_isp_profile, args.timeout
    )
    try:
        device = inspect_bootloader(client)
        device["port"] = args.port
        device["auto_isp_profile"] = profile.name
        device["operation_class"] = "read-only"

        if args.command == "probe":
            _emit(device)
            return 0

        image = read_factory_flash(client, progress=sys.stderr.buffer)
        validation = validate_factory_image(image)
        save_new_file(args.output, image)
        _emit(
            {
                **device,
                **validation,
                "flash_base": f"0x{FLASH_BASE:08X}",
                "flash_end_exclusive": f"0x{FLASH_END:08X}",
                "output": str(args.output.expanduser().resolve()),
                "validated": True,
            }
        )
        return 0
    finally:
        adapter.restore_run_lines(profile)
        adapter.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only STM32F407 ROM-UART probe and factory backup"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("probe", "backup"):
        command = subparsers.add_parser(name)
        command.add_argument("--port", required=True)
        command.add_argument(
            "--auto-isp-profile",
            choices=("auto",) + tuple(p.name for p in AUTO_ISP_PROFILES),
            default="inverted-both",
        )
        command.add_argument("--timeout", type=float, default=0.75)
        if name == "backup":
            command.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return _run_hardware(args)
    except (BootloaderError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
