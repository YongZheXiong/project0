#!/usr/bin/env python3
"""Run the Project0 no-Orin W0 fake-serial web teleop server."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _ensure_package_path() -> None:
    root = Path(__file__).resolve().parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


_ensure_package_path()

from no_orin_web_teleop.server import run_server, validate_bind_host  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--log-jsonl", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        host = validate_bind_host(args.host)
    except ValueError as error:
        print(f"refusing to start: {error}", file=sys.stderr)
        return 2
    print("Project0 W0 fake-serial web teleop")
    print("No real H60 serial port is opened by this server.")
    print(f"URL: http://{host}:{args.port}/")
    run_server(host=host, port=args.port, log_jsonl=args.log_jsonl)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
