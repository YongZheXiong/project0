#!/usr/bin/env python3
"""Read-only Project0 stage/version consistency reminder."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


STAGE_VERSION = {
    "P0": "v0.1", "P1": "v0.2", "P2": "v1.1", "P3": "v1.2",
    "P4": "v1.3", "P5": "v1.4", "P6": "v1.5", "P7": "v2.1",
    "P8": "v2.2", "P9": "v2.3", "P10": "v2.4",
}


def git_tags(repo: Path) -> list[str]:
    result = subprocess.run(
        ["git", "tag", "--list"], cwd=repo, text=True, capture_output=True, check=False
    )
    return sorted(line for line in result.stdout.splitlines() if line)


def git_status_count(repo: Path) -> int:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    return len(result.stdout.splitlines())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    readme = (repo / "README.md").read_text(encoding="utf-8")
    changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    gate = (repo / "docs/06_testing/p2_h60_mc520_rebuild_acceptance_plan_2026-08-16.md").read_text(
        encoding="utf-8"
    )

    stage_match = re.search(r"\| (?:当前阶段|阶段与版本) \|\s*(P\d+)", readme)
    version_match = re.search(r"\| (?:当前版本|阶段与版本) \|\s*([^|]+)\|", readme)
    stage = stage_match.group(1) if stage_match else None
    version_text = version_match.group(1).strip() if version_match else None
    expected_release = STAGE_VERSION.get(stage or "")
    expected_development = f"{expected_release}-dev" if expected_release else None
    tags = git_tags(repo)
    development_tags = sorted(
        (
            tag
            for tag in tags
            if expected_development
            and re.fullmatch(rf"{re.escape(expected_development)}\.(\d+)", tag)
        ),
        key=lambda tag: int(tag.rsplit(".", 1)[1]),
    )
    latest_development_tag = development_tags[-1] if development_tags else None
    worktree_change_count = git_status_count(repo)
    errors: list[str] = []
    reminders: list[str] = []

    if stage is None:
        errors.append("README 未识别到当前 P 阶段")
    if expected_development and expected_development not in (version_text or ""):
        errors.append(f"README 当前阶段 {stage} 应使用 {expected_development} / Unreleased")
    if "## [Unreleased]" not in changelog:
        errors.append("CHANGELOG 缺少 Unreleased 入口")
    if expected_development and expected_development not in changelog:
        errors.append(f"CHANGELOG 缺少 {expected_development} 的 Unreleased 入口")
    if latest_development_tag and f"[{latest_development_tag}]" not in changelog:
        errors.append(f"CHANGELOG 缺少已存在标签 {latest_development_tag} 的版本节")

    gate_rows = dict(
        re.findall(r"^\| (H[0-8]) \|.*\| ([A-Z ]+) \|$", gate, re.MULTILINE)
    )
    p2_gate_complete = len(gate_rows) == 9 and all(
        status == "PASS" for status in gate_rows.values()
    )
    expected_tag_present = expected_release in tags if expected_release else False

    if stage == "P2" and expected_tag_present and not p2_gate_complete:
        errors.append("检测到 v1.1 标签，但 H0-H8 尚未全部 PASS")
    if stage == "P2" and p2_gate_complete and not expected_tag_present:
        reminders.append(
            "H0-H8 已全部 PASS：进入 v1.1 发布审查；仍需人工复核真实代码、"
            "通信/里程计/接管证据、阶段记录、CHANGELOG、发布 diff 和用户授权"
        )
    elif stage == "P2":
        reminders.append("P2 尚未完成：保持 v1.1-dev / Unreleased，不发布 v1.1")
        if latest_development_tag:
            reminders.append(f"最新开发预发布为 {latest_development_tag}；该标签不表示 P2 完成")

    if worktree_change_count:
        reminders.append(f"工作区有 {worktree_change_count} 条未提交状态：发布前需审查并收束")

    if "v0.2.9" in tags:
        reminders.append("检测到历史标签 v0.2.9：未经单独批准不得删除或重写")

    if errors:
        release_state = "CONSISTENCY_ERROR"
    elif expected_tag_present and p2_gate_complete:
        release_state = "RELEASE_TAG_PRESENT"
    elif p2_gate_complete:
        release_state = "STAGE_GATE_COMPLETE_REVIEW_REQUIRED"
    elif latest_development_tag:
        release_state = "DEVELOPMENT_PRERELEASE_TAG_PRESENT"
    else:
        release_state = "DEVELOPMENT"

    payload = {
        "stage": stage,
        "version_text": version_text,
        "expected_release": expected_release,
        "tags": tags,
        "development_tags": development_tags,
        "latest_development_tag": latest_development_tag,
        "p2_gate_statuses": gate_rows,
        "p2_gate_complete": p2_gate_complete,
        "worktree_change_count": worktree_change_count,
        "release_state": release_state,
        "manual_release_review": [
            "H60 与 Orin 侧真实代码可复现",
            "通信、里程计、停车/故障处置和人工接管证据完整",
            "P2 阶段记录、证据索引和 CHANGELOG 已收束",
            "发布 diff、工作区、目标标签和用户授权已复核",
        ],
        "errors": errors,
        "reminders": reminders,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            f"stage={stage or 'UNKNOWN'} expected_release={expected_release or 'UNKNOWN'} "
            f"release_state={release_state}"
        )
        for item in errors:
            print(f"ERROR: {item}")
        for item in reminders:
            print(f"REMINDER: {item}")
        print("RESULT: FAIL" if errors else "RESULT: PASS")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
