"""Small raw 8N1 POSIX serial adapter with no third-party dependency."""

from __future__ import annotations

import os
import select
import termios
import threading


_BAUD_RATES = {
    9600: termios.B9600,
    19200: termios.B19200,
    38400: termios.B38400,
    57600: termios.B57600,
    115200: termios.B115200,
}


class PosixSerialPort:
    """Raw 8N1 serial port for the Orin Linux runtime.

    ``readline`` and ``write_line`` remain only for legacy offline regression
    tests.  The active H60 bridge uses ``read`` and ``write`` exclusively.
    """

    def __init__(self, device: str, baud_rate: int) -> None:
        if baud_rate not in _BAUD_RATES:
            raise ValueError(f"unsupported baud rate: {baud_rate}")
        self._lock = threading.Lock()
        self._rx_buffer = bytearray()
        self._fd = os.open(device, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        try:
            attributes = termios.tcgetattr(self._fd)
            attributes[0] = 0
            attributes[1] = 0
            attributes[2] = termios.CLOCAL | termios.CREAD | termios.CS8
            attributes[3] = 0
            attributes[4] = _BAUD_RATES[baud_rate]
            attributes[5] = _BAUD_RATES[baud_rate]
            attributes[6][termios.VMIN] = 0
            attributes[6][termios.VTIME] = 0
            termios.tcsetattr(self._fd, termios.TCSANOW, attributes)
            termios.tcflush(self._fd, termios.TCIOFLUSH)
        except Exception:
            os.close(self._fd)
            self._fd = -1
            raise

    def read(self, max_bytes: int, timeout_sec: float) -> bytes:
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        if timeout_sec < 0.0:
            raise ValueError("timeout_sec must be non-negative")
        fd = self._fd
        if fd < 0:
            raise OSError("serial port is closed")
        readable, _, _ = select.select([fd], [], [], timeout_sec)
        if not readable:
            return b""
        return os.read(fd, max_bytes)

    def write(self, payload: bytes, timeout_sec: float = 0.10) -> None:
        data = bytes(payload)
        if timeout_sec <= 0.0:
            raise ValueError("timeout_sec must be positive")
        with self._lock:
            if self._fd < 0:
                raise OSError("serial port is closed")
            total = 0
            while total < len(data):
                _, writable, _ = select.select([], [self._fd], [], timeout_sec)
                if not writable:
                    raise TimeoutError("serial write timeout")
                total += os.write(self._fd, data[total:])

    def readline(self, timeout_sec: float) -> bytes:
        while True:
            newline = self._rx_buffer.find(b"\n")
            if newline >= 0:
                line = bytes(self._rx_buffer[: newline + 1])
                del self._rx_buffer[: newline + 1]
                return line

            fd = self._fd
            if fd < 0:
                raise OSError("serial port is closed")
            readable, _, _ = select.select([fd], [], [], timeout_sec)
            if not readable:
                return b""
            chunk = os.read(fd, 1024)
            if chunk:
                self._rx_buffer.extend(chunk)

    def write_line(self, line: str) -> None:
        self.write((line + "\n").encode("ascii"))

    def close(self) -> None:
        with self._lock:
            if self._fd >= 0:
                fd = self._fd
                self._fd = -1
                os.close(fd)
