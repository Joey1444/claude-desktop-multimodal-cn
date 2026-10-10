#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CI 校验：配置示例的 JSON 合法性、必备文件存在、相对链接有效、无密钥泄漏。

在本地和 GitHub Actions 里跑同一份。
用法：python3 scripts/ci_check.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


# 1. 所有 JSON 必须能解析
for p in sorted(ROOT.rglob("*.json")):
    if ".git" in p.parts:
        continue
    try:
        json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        fail(f"{p.relative_to(ROOT)}：JSON 解析失败 —— {e}")

# 2. 必备文件
for rel in ("README.md", "LICENSE", ".gitignore",
            "article/平台版-掘金知乎.md", "article/发布信息.md",
            "configs/claude_desktop_config.example.json"):
    if not (ROOT / rel).is_file():
        fail(f"缺文件：{rel}")

# 3. Markdown 里的相对链接要指向真实存在的文件
LINK = re.compile(r"\[[^\]]*\]\(([^)#]+?)\)")
for md in sorted(ROOT.rglob("*.md")):
    if ".git" in md.parts:
        continue
    for target in LINK.findall(md.read_text(encoding="utf-8")):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        resolved = (md.parent / target).resolve()
        if not resolved.exists():
            fail(f"{md.relative_to(ROOT)}：相对链接失效 -> {target}")

# 4. 不许有密钥
PATTERNS = [
    (re.compile(r"sk-or-v1-[A-Za-z0-9]{16,}"), "OpenRouter key"),
    (re.compile(r"ghp_[A-Za-z0-9]{20,}"), "GitHub PAT"),
    (re.compile(r"sk-[A-Za-z0-9]{32,}"), "OpenAI-style key"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "私钥"),
]
SKIP_SUFFIX = {".png", ".jpg", ".jpeg", ".gif", ".zip", ".mp3", ".mp4"}
for p in sorted(ROOT.rglob("*")):
    if not p.is_file() or ".git" in p.parts or p.suffix.lower() in SKIP_SUFFIX:
        continue
    if p.name == Path(__file__).name:
        continue
    try:
        text = p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        continue
    for rx, label in PATTERNS:
        m = rx.search(text)
        if m:
            fail(f"{p.relative_to(ROOT)}：疑似泄漏 {label}（{m.group(0)[:12]}…）")


if errors:
    print("CI 校验未通过：\n")
    for e in errors:
        print("  ✗", e)
    sys.exit(1)

print("CI 校验通过：JSON / 必备文件 / 相对链接 / 密钥扫描 全部 OK")
