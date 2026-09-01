#!/usr/bin/env python3

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "tools" / "stm32_uart_bootloader.py"
SPEC = importlib.util.spec_from_file_location("stm32_uart_bootloader", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
boot = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = boot
SPEC.loader.exec_module(boot)


class FakeTransport:
    def __init__(self, replies: bytes):
        self.replies = bytearray(replies)
        self.writes = []

    def write(self, data: bytes) -> int:
        self.writes.append(bytes(data))
        return len(data)

    def read(self, size: int) -> bytes:
        result = bytes(self.replies[:size])
        del self.replies[:size]
        return result


class BootloaderProtocolTests(unittest.TestCase):
    def test_sync_and_get_id(self):
        transport = FakeTransport(
            bytes((boot.ACK, boot.ACK, 0x01, 0x04, 0x13, boot.ACK))
        )
        client = boot.STM32Bootloader(transport)
        client.sync()
        chip_id, raw_id = client.get_id()
        self.assertEqual(chip_id, 0x0413)
        self.assertEqual(raw_id, b"\x04\x13")
        self.assertEqual(
            transport.writes,
            [b"\x7F", bytes((boot.CMD_GET_ID, boot.CMD_GET_ID ^ 0xFF))],
        )

    def test_get_supported_commands(self):
        response = bytes(
            (
                boot.ACK,
                0x03,
                0x31,
                boot.CMD_GET,
                boot.CMD_GET_ID,
                boot.CMD_READ_MEMORY,
                boot.ACK,
            )
        )
        client = boot.STM32Bootloader(FakeTransport(response))
        version, commands = client.get()
        self.assertEqual(version, 0x31)
        self.assertEqual(
            commands, (boot.CMD_GET, boot.CMD_GET_ID, boot.CMD_READ_MEMORY)
        )

    def test_read_memory_encodes_address_and_length(self):
        data = b"\x12\x34\x56\x78"
        transport = FakeTransport(
            bytes((boot.ACK, boot.ACK, boot.ACK)) + data
        )
        client = boot.STM32Bootloader(transport)
        self.assertEqual(client.read_memory(boot.FLASH_BASE + 0x20, 4), data)
        address = (boot.FLASH_BASE + 0x20).to_bytes(4, "big")
        self.assertEqual(
            transport.writes,
            [
                bytes((boot.CMD_READ_MEMORY, boot.CMD_READ_MEMORY ^ 0xFF)),
                address + bytes((boot._xor_bytes(address),)),
                b"\x03\xFC",
            ],
        )

    def test_read_rejects_out_of_range_access(self):
        client = boot.STM32Bootloader(FakeTransport(b""))
        with self.assertRaises(boot.BootloaderError):
            client.read_memory(boot.FLASH_END - 128, 256)

    def test_timeout_is_an_error(self):
        client = boot.STM32Bootloader(FakeTransport(b""))
        with self.assertRaises(boot.BootloaderError):
            client.sync()


class BackupValidationTests(unittest.TestCase):
    @staticmethod
    def valid_image() -> bytearray:
        image = bytearray(b"\xFF" * boot.FLASH_SIZE)
        image[0:4] = (0x2001FFF0).to_bytes(4, "little")
        image[4:8] = (boot.FLASH_BASE + 0x101).to_bytes(4, "little")
        image[0x100:0x108] = b"FACTORY!"
        return image

    def test_valid_vector_table_and_hash(self):
        result = boot.validate_factory_image(bytes(self.valid_image()))
        self.assertEqual(result["bytes"], boot.FLASH_SIZE)
        self.assertEqual(result["initial_msp"], "0x2001FFF0")
        self.assertEqual(result["reset_vector"], "0x08000101")
        self.assertEqual(len(result["sha256"]), 64)

    def test_accepts_exclusive_ram_end_as_initial_msp(self):
        for initial_msp in (0x20020000, 0x10010000):
            with self.subTest(initial_msp=f"0x{initial_msp:08X}"):
                image = self.valid_image()
                image[0:4] = initial_msp.to_bytes(4, "little")
                result = boot.validate_factory_image(bytes(image))
                self.assertEqual(result["initial_msp"], f"0x{initial_msp:08X}")

    def test_rejects_initial_msp_above_ram_end(self):
        image = self.valid_image()
        image[0:4] = (0x20020004).to_bytes(4, "little")
        with self.assertRaises(boot.BootloaderError):
            boot.validate_factory_image(bytes(image))

    def test_rejects_blank_image(self):
        with self.assertRaises(boot.BootloaderError):
            boot.validate_factory_image(b"\xFF" * boot.FLASH_SIZE)

    def test_rejects_non_thumb_reset_vector(self):
        image = self.valid_image()
        image[4:8] = (boot.FLASH_BASE + 0x100).to_bytes(4, "little")
        with self.assertRaises(boot.BootloaderError):
            boot.validate_factory_image(bytes(image))

    def test_save_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "factory.bin"
            boot.save_new_file(path, b"first")
            with self.assertRaises(boot.BootloaderError):
                boot.save_new_file(path, b"second")
            self.assertEqual(path.read_bytes(), b"first")


if __name__ == "__main__":
    unittest.main()
