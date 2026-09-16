#!/usr/bin/env python3

import importlib.util
import json
import sys
import tempfile
import unittest
from unittest import mock
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

    def test_read_memory_timeout_identifies_address_ack_phase(self):
        trace = []
        transport = FakeTransport(bytes((boot.ACK,)))
        client = boot.STM32Bootloader(transport, trace=trace.append)

        with self.assertRaises(boot.ReadMemoryError) as raised:
            client.read_memory(boot.FLASH_BASE + 0x35700, boot.READ_CHUNK)

        self.assertEqual(raised.exception.address, boot.FLASH_BASE + 0x35700)
        self.assertEqual(raised.exception.phase, "address_ack")
        self.assertIn("READ MEMORY address ACK", raised.exception.cause)
        self.assertEqual(len(trace), 1)
        self.assertEqual(trace[0]["status"], "error")
        self.assertEqual(trace[0]["failed_phase"], "address_ack")
        self.assertEqual(
            [item["phase"] for item in trace[0]["phases"]],
            ["command_write", "command_ack", "address_write", "address_ack"],
        )

    def test_read_memory_identifies_every_response_phase(self):
        cases = (
            (b"", "command_ack"),
            (bytes((boot.ACK,)), "address_ack"),
            (bytes((boot.ACK, boot.ACK)), "length_ack"),
            (bytes((boot.ACK, boot.ACK, boot.ACK, 0x5A)), "data"),
        )
        for replies, expected_phase in cases:
            with self.subTest(expected_phase=expected_phase):
                trace = []
                client = boot.STM32Bootloader(
                    FakeTransport(replies), trace=trace.append
                )
                with self.assertRaises(boot.ReadMemoryError) as raised:
                    client.read_memory(boot.FLASH_BASE, boot.READ_CHUNK)
                self.assertEqual(raised.exception.phase, expected_phase)
                self.assertEqual(trace[0]["failed_phase"], expected_phase)

    def test_full_read_failure_does_not_replay_transaction(self):
        transport = FakeTransport(b"")
        client = boot.STM32Bootloader(transport)

        with self.assertRaises(boot.FlashReadError) as raised:
            boot.read_factory_flash(client)

        self.assertEqual(raised.exception.completed_bytes, 0)
        self.assertEqual(raised.exception.transaction_error.phase, "command_ack")
        self.assertEqual(
            transport.writes,
            [bytes((boot.CMD_READ_MEMORY, boot.CMD_READ_MEMORY ^ 0xFF))],
        )

    def test_full_read_failure_retains_completed_prefix(self):
        first_block = bytes(range(256))
        replies = bytes((boot.ACK, boot.ACK, boot.ACK)) + first_block
        client = boot.STM32Bootloader(FakeTransport(replies))

        with self.assertRaises(boot.FlashReadError) as raised:
            boot.read_factory_flash(client)

        self.assertEqual(raised.exception.completed_bytes, boot.READ_CHUNK)
        self.assertEqual(raised.exception.partial_image, first_block)
        self.assertEqual(
            raised.exception.transaction_error.address,
            boot.FLASH_BASE + boot.READ_CHUNK,
        )
        self.assertEqual(raised.exception.transaction_error.phase, "command_ack")

    def test_jsonl_trace_flushes_failed_transaction(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "read.transactions.jsonl"
            trace = boot.JsonlTrace(path)
            client = boot.STM32Bootloader(FakeTransport(b""), trace=trace)
            with self.assertRaises(boot.ReadMemoryError):
                client.read_memory(boot.FLASH_BASE, boot.READ_CHUNK)
            trace.close()

            records = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(len(records), 1)
            self.assertEqual(
                records[0]["schema"],
                "project0.stm32_rom_uart_read_transaction.v1",
            )
            self.assertEqual(records[0]["address"], "0x08000000")
            self.assertEqual(records[0]["failed_phase"], "command_ack")


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

    def test_hardware_runner_saves_partial_prefix_without_full_image(self):
        class FakeAdapter:
            def restore_run_lines(self, _profile):
                return None

            def close(self):
                return None

        class FailingClient:
            def __init__(self):
                self.calls = 0

            def get_id(self):
                return boot.EXPECTED_CHIP_ID, b"\x04\x13"

            def get(self):
                return 0x31, (boot.CMD_READ_MEMORY,)

            def read_memory(self, address, size):
                self.calls += 1
                if self.calls == 1:
                    return bytes(range(size))
                raise boot.ReadMemoryError(
                    address=address,
                    size=size,
                    phase="command_ack",
                    cause="synthetic timeout",
                    phases=[
                        {"phase": "command_write", "status": "pass"},
                        {"phase": "command_ack", "status": "error"},
                    ],
                )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "factory.bin"
            args = boot.build_parser().parse_args(
                ["backup", "--port", "synthetic", "--output", str(output)]
            )
            profile = boot.AUTO_ISP_PROFILES[0]
            client = FailingClient()
            with mock.patch.object(
                boot,
                "connect_read_only",
                return_value=(FakeAdapter(), client, profile),
            ):
                with self.assertRaises(boot.BootloaderError) as raised:
                    boot._run_hardware(args)

            partial = root / "factory.bin.partial"
            trace = root / "factory.bin.transactions.jsonl"
            self.assertFalse(output.exists())
            self.assertEqual(partial.read_bytes(), bytes(range(256)))
            self.assertTrue(trace.exists())
            self.assertIn("no automatic transaction replay", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
